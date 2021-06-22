from typing import Deque, Union, Optional, List

from hwt.code import Concat
from hwt.hdl.types.bitsVal import BitsVal
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.structValBase import StructValBase
from hwt.hdl.value import HValue
from hwt.synthesizer.rtlLevel.constants import NOT_SPECIFIED
from hwtLib.peripheral.usb.constants import USB_PID
from hwtLib.peripheral.usb.descriptors.bundle import UsbDescriptorBundle, \
    UsbNoSuchDescriptor
from hwtLib.peripheral.usb.descriptors.cdc import usb_descriptor_functional_header, \
    USB_CDC_DESCRIPTOR_SUBTYPE, usb_descriptor_functional_header_t, \
    usb_descriptor_functional_call_management_t, \
    usb_descriptor_functional_abstract_control_management_t, \
    usb_define_descriptor_functional_union_t
from hwtLib.peripheral.usb.descriptors.std import usb_descriptor_interface_t, \
    USB_DEVICE_CLASS, usb_descriptor_header_t, USB_DESCRIPTOR_TYPE, \
    usb_descriptor_configuration_t, usb_descriptor_endpoint_t, \
    make_usb_device_request_get_descr, usb_define_descriptor_string, \
    usb_descriptor_device_t, usb_descriptor_device_qualifier_t, \
    usb_define_descriptor_string0
from hwtLib.peripheral.usb.device_requiest import make_usb_device_request, \
    USB_REQUEST_TYPE_RECIPIENT, USB_REQUEST_TYPE_TYPE, \
    USB_REQUEST_TYPE_DIRECTION, USB_REQUEST
from hwtLib.peripheral.usb.sim.agent_base import UsbAgent, UsbPacketToken, \
    UsbPacketData, UsbPacketHandshake
from hwtLib.types.ctypes import uint8_t


class UsbHostAgent(UsbAgent):
    """
    This agent uses rx and tx queue to comunicate with a USB device.
    It performs bus enumerations, sets address to a device and downloads
    the descriptors. Note that the agent is written in a way which allows for easy
    extension to a driver which can parse the specific descriptors and comunicate with devices further.
    """

    def __init__(self,
             rx: Deque[Union[UsbPacketToken, UsbPacketHandshake, UsbPacketData]],
             tx: Deque[Union[UsbPacketToken, UsbPacketHandshake, UsbPacketData]]):
        super(UsbHostAgent, self).__init__(rx, tx)
        # the addresses are not asigned yet this dictionary will be filled during device enumeration
        self.descr = {}

    def receive_data(self, addr: int, endp: int, pid_init: USB_PID, size:int):
        ddb = self.descr.get(addr, None)
        if ddb is None:
            maxPacketLen = 8
        else:
            if endp == 0:
                d = ddb.get_descriptor(usb_descriptor_device_t, 0)[1]
                maxPacketLen = int(d.body.bMaxPacketSize)
            else:
                raise NotImplementedError()

        pid = pid_init
        # start recieveing the data
        yield from self.send(UsbPacketToken(USB_PID.TOKEN_IN, addr, endp))
        # can receive data or STALL if the descriptor is not present
        d_raw = yield from self.receive(NOT_SPECIFIED)
        if isinstance(d_raw, UsbPacketData):
            assert d_raw.pid == pid, (d_raw.pid, pid)
            # descriptor data
            yield from self.send_ack()
            if len(d_raw.data) >= maxPacketLen:
                # coud be possibly split into multiple packets
                while len(d_raw.data) != size:
                    if pid == USB_PID.DATA_0:
                        pid = USB_PID.DATA_1
                    elif pid == USB_PID.DATA_1:
                        pid = USB_PID.DATA_0
                    else:
                        raise NotImplementedError(pid)

                    yield from self.send(UsbPacketToken(USB_PID.TOKEN_IN, addr, endp))
                    descr_part = yield from self.receive(UsbPacketData)
                    assert descr_part.pid == pid, (d_raw.pid, pid)
                    d_raw.data.extend(descr_part.data)
                    yield from self.send_ack()
                    if len(descr_part.data) < maxPacketLen:
                        break
            return d_raw.data

        elif isinstance(d_raw, UsbPacketHandshake):
            # packet which means some error
            if d_raw.pid == USB_PID.HS_STALL:
                raise UsbNoSuchDescriptor()
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

    def parse_interface_descriptor(self, first_interface_descr: StructValBase, data:BitsVal):
        if first_interface_descr is None:
            t = usb_descriptor_interface_t
            assert data._dtype.bit_length() == t.bit_length()
            return data._reinterpret_cast(t)
        else:
            bInterfaceClass = int(first_interface_descr.body.bInterfaceClass)
            if bInterfaceClass == USB_DEVICE_CLASS.CDC_CONTROL:
                h_t = usb_descriptor_functional_header
                header = data[h_t.bit_length():]._reinterpret_cast(h_t)
                sub_t = int(header.bDescriptorSubtype)
                if sub_t == USB_CDC_DESCRIPTOR_SUBTYPE.HEADER:
                    descr_t = usb_descriptor_functional_header_t
                elif sub_t == USB_CDC_DESCRIPTOR_SUBTYPE.CALL_MANAGEMENT_FUNCTIONAL:
                    descr_t = usb_descriptor_functional_call_management_t
                elif sub_t == USB_CDC_DESCRIPTOR_SUBTYPE.ABSTRACT_CONTROL_MANAGEMENT:
                    descr_t = usb_descriptor_functional_abstract_control_management_t
                elif sub_t == USB_CDC_DESCRIPTOR_SUBTYPE.UNION:
                    slave_cnt = (data._dtype.bit_length() - h_t.bit_length() - 8) // 8
                    descr_t = usb_define_descriptor_functional_union_t(slave_cnt)

                assert data._dtype.bit_length() == descr_t.bit_length()
                return data._reinterpret_cast(descr_t)
            else:
                raise NotImplementedError()

    def parse_configuration_descriptor_bundle(self, data_bytes: List[int]):
        data = [d if isinstance(d, HValue) else uint8_t.from_py(d) for d in data_bytes]
        data = Concat(*reversed(data))
        offset = 0
        end = data._dtype.bit_length()
        header_width = usb_descriptor_header_t.bit_length()

        descriptors = []
        first_interface_descr = None
        while offset < end:
            header = data[header_width + offset: offset]
            header = header._reinterpret_cast(usb_descriptor_header_t)
            descr_typeId = int(header.bDescriptorType)
            descr_width = int(header.bLength) * 8
            try:
                d = data[descr_width + offset: offset]
            except IndexError:
                raise IndexError("The input data is incomplete, the header suggest additional data",
                                 offset, descr_width, end)

            if descr_typeId == USB_DESCRIPTOR_TYPE.CONFIGURATION:
                t = usb_descriptor_configuration_t
                assert descr_width == t.bit_length()
                d = d._reinterpret_cast(t)
                first_interface_descr = None
            elif descr_typeId == USB_DESCRIPTOR_TYPE.INTERFACE:
                # :note: interface descriptors are class dependent,
                #        the class can be resolved from first interface descriptor
                #        next interface descriptors may be functional descriptors
                d = self.parse_interface_descriptor(first_interface_descr, d)
                if first_interface_descr is None:
                    first_interface_descr = d
            elif descr_typeId == USB_DESCRIPTOR_TYPE.ENDPOINT:
                t = usb_descriptor_endpoint_t
                assert descr_width == t.bit_length()
                d = d._reinterpret_cast(t)
                first_interface_descr = None
            else:
                raise NotImplementedError(descr_typeId)
            descriptors.append(d)
            offset += descr_width

        return descriptors

    def download_descriptor(self,
                            addr: int,
                            descriptor_t: Union[HStruct, str],
                            index: int,
                            wIndex:int=0,
                            wLength: Optional[int]=NOT_SPECIFIED):
        dev_req_get_descr = make_usb_device_request_get_descr(
            descriptor_t, index, wIndex=wIndex, wLength=wLength)

        # read the device descriptor
        # SETUP STAGE, send request for descriptor downloading
        yield from self.send(UsbPacketToken(USB_PID.TOKEN_SETUP, addr, 0))
        yield from self.send(UsbPacketData(USB_PID.DATA_0, dev_req_get_descr))
        yield from self.wait_on_ack()

        # DATA stage
        descr = yield from self.receive_data(addr, 0, USB_PID.DATA_1, int(dev_req_get_descr.wLength))
        if wLength is NOT_SPECIFIED:
            if descriptor_t is str:
                char_cnt = (len(descr) - usb_descriptor_header_t.bit_length() // 8) // 2
                if index == 0:
                    descriptor_t = usb_define_descriptor_string0(char_cnt)
                else:
                    descriptor_t = usb_define_descriptor_string(char_cnt)
            descr = UsbPacketData(USB_PID.DATA_1, descr)
            descr = descr.unpack(descriptor_t)
        else:
            assert len(descr) == int(dev_req_get_descr.wLength), (len(descr), int(dev_req_get_descr.wLength))
            assert descriptor_t is usb_descriptor_configuration_t, descriptor_t
            descr = self.parse_configuration_descriptor_bundle(descr)

        # STATUS stage
        yield from self.send(UsbPacketToken(USB_PID.TOKEN_OUT, addr, 0))
        yield from self.send(UsbPacketData(USB_PID.DATA_1, []))
        yield from self.wait_on_ack()
        return descr

    def proc(self):
        # query EP 0
        p = UsbPacketToken(USB_PID.TOKEN_SETUP, 0, 0)
        yield from self.send(p)

        new_addr = len(self.descr) + 1
        # init device address
        set_addr = make_usb_device_request(
            bmRequestType_recipient=USB_REQUEST_TYPE_RECIPIENT.DEVICE,
            bmRequestType_type=USB_REQUEST_TYPE_TYPE.STANDARD,
            bmRequestType_data_transfer_direction=USB_REQUEST_TYPE_DIRECTION.HOST_TO_DEV,
            bRequest=USB_REQUEST.SET_ADDRESS,
            wValue=new_addr,
            wIndex=0,
            wLength=0)

        yield from self.send(UsbPacketData(USB_PID.DATA_0, set_addr))
        yield from self.wait_on_ack()
        yield from self.send(UsbPacketToken(USB_PID.TOKEN_IN, 0, 0))
        after_addr_set_empty_in = yield from self.receive(UsbPacketData)  # STATUS stage
        yield from self.send_ack()
        assert after_addr_set_empty_in.pid == USB_PID.DATA_1 and not after_addr_set_empty_in.data
        # :note: device address now set, starting download of descriptors

        dev_descr = yield from self.download_descriptor(new_addr, usb_descriptor_device_t, 0)

        ddb = self.descr[new_addr] = UsbDescriptorBundle()
        ddb.append(dev_descr)

        bNumConfigurations = int(dev_descr.body.bNumConfigurations)
        assert bNumConfigurations > 0, "Device must have some configuration descriptors"
        for i in range(bNumConfigurations):
            # first we have to resolve wTotalLength (the total lenght of configuration bundle)
            conf_descr = yield from self.download_descriptor(new_addr, usb_descriptor_configuration_t, i)
            size = int(conf_descr.body.wTotalLength)
            # now we download all descriptors in configuration bundle
            conf_descr_bundle = yield from self.download_descriptor(
                new_addr, usb_descriptor_configuration_t, i, wLength=size)
            real_size = sum(c._dtype.bit_length() for c in conf_descr_bundle) // 8
            assert real_size == size, (real_size, size, conf_descr_bundle)
            ddb.extend(conf_descr_bundle)

        while True:
            try:
                yield from self.download_descriptor(
                    new_addr, usb_descriptor_device_qualifier_t, 0
                )
            except UsbNoSuchDescriptor:
                break
            raise NotImplementedError("usb_descriptor_device_qualifier")
        # now read all string descriptors
        str_descr0 = None
        for i in range(0, 255):
            try:
                str_descr = yield from self.download_descriptor(
                    new_addr, str, i,
                    wIndex=0 if i == 0 else int(str_descr0.body[0])
                )
            except UsbNoSuchDescriptor:
                if i == 0:
                    raise UsbNoSuchDescriptor("Need at least string descriptor 0 with language code")
                else:
                    # other are not required
                    break

            if i == 0:
                str_descr0 = str_descr
            ddb.append(str_descr)
