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
    usb_define_descriptor_string0, USB_ENDPOINT_DIR
from hwtLib.peripheral.usb.device_request import make_usb_device_request, \
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
        self._descriptors_downloaded = False

    def parse_interface_functional_descriptor(self, interface_descr: StructValBase, data:BitsVal):
        bInterfaceClass = int(interface_descr.body.bInterfaceClass)
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
        interface_descr = None
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
                interface_descr = None
            elif descr_typeId == USB_DESCRIPTOR_TYPE.INTERFACE:
                # :note: interface descriptors are class dependent,
                #        the class can be resolved from first interface descriptor
                #        next interface descriptors may be functional descriptors
                t = usb_descriptor_interface_t
                assert d._dtype.bit_length() == t.bit_length(), (d._dtype.bit_length(), t.bit_length())
                d = d._reinterpret_cast(t)
                interface_descr = d
            elif descr_typeId == USB_DESCRIPTOR_TYPE.ENDPOINT:
                t = usb_descriptor_endpoint_t
                assert descr_width == t.bit_length()
                d = d._reinterpret_cast(t)
            elif descr_typeId == USB_DESCRIPTOR_TYPE.FUNCTIONAL:
                d = self.parse_interface_functional_descriptor(interface_descr, d)
            else:
                raise NotImplementedError(descr_typeId)
            descriptors.append(d)
            offset += descr_width

        return descriptors

    def get_max_packet_size(self, addr:int, endp: int, direction: USB_ENDPOINT_DIR):
        ddb: UsbDescriptorBundle = self.descr.get(addr, None)
        if ddb is None:
            max_packet_size = 64
        else:
            if endp == 0:
                d = ddb.get_descriptor(usb_descriptor_device_t, 0)[1]
                max_packet_size = int(d.body.bMaxPacketSize)
            else:
                max_packet_size = None
                for des in ddb:
                    if des._dtype == usb_descriptor_endpoint_t and \
                        int(des.body.bEndpointAddress) == endp and \
                        int(des.body.bEndpointAddressDir) == direction:
                        max_packet_size = int(des.body.wMaxPacketSize)
                        break
                if max_packet_size is None:
                    raise ValueError("Can not find configuration for endpoint in descriptors", endp, ddb)
        return max_packet_size

    def receive_bulk(self, addr: int, endp: int, pid_init: USB_PID, size=NOT_SPECIFIED) -> List[int]:
        max_packet_size = self.get_max_packet_size(addr, endp, USB_ENDPOINT_DIR.IN)

        pid = pid_init
        # start recieveing the data
        yield from self.send(UsbPacketToken(USB_PID.TOKEN_IN, addr, endp))
        # can receive data or STALL if the descriptor is not present
        d_raw = yield from self.receive(NOT_SPECIFIED)
        if isinstance(d_raw, UsbPacketData):
            assert d_raw.pid == pid, (d_raw.pid, pid)
            # descriptor data
            yield from self.send_ack()
            if size is not NOT_SPECIFIED:
                return d_raw.data

            # could be actually larger in the case when EP0 is not configured yet
            if len(d_raw.data) >= max_packet_size:
                # coud be possibly split into multiple packets
                # if the first chunk was just of pmax_packet_size and this is the size what we are asking for
                while True:
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
                    if len(descr_part.data) < max_packet_size:
                        break

            return d_raw.data

        elif isinstance(d_raw, UsbPacketHandshake):
            # packet which means some error
            if d_raw.pid == USB_PID.HS_STALL:
                raise UsbNoSuchDescriptor()
            elif d_raw.pid == USB_PID.HS_NACK:
                return None
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

    def transmit_bulk(self, addr: int, endp: int, pid_init: USB_PID, data_bytes: List[int]):
        max_packet_size = self.get_max_packet_size(addr, endp, USB_ENDPOINT_DIR.OUT)

        pid = pid_init
        # start sending the data
        begin = 0
        end = len(data_bytes)
        while True:
            yield from self.send(UsbPacketToken(USB_PID.TOKEN_OUT, addr, endp))
            _end = min(begin + max_packet_size, end)
            p = UsbPacketData(pid, data_bytes[begin:_end])
            yield from self.send(p)
            yield from self.wait_on_ack()

            begin = _end
            if pid == USB_PID.DATA_0:
                pid = USB_PID.DATA_1
            elif pid == USB_PID.DATA_1:
                pid = USB_PID.DATA_0
            else:
                raise ValueError(pid)

            if len(p.data) < max_packet_size:
                break

    def control_read(self, addr, bmRequestType_type:USB_REQUEST_TYPE_TYPE, bRequest:int,
                     wValue:int, wIndex:int, wLength:int,
                     bmRequestType_recipient:USB_REQUEST_TYPE_RECIPIENT=USB_REQUEST_TYPE_RECIPIENT.DEVICE,
                     bmRequestType_data_transfer_direction:USB_REQUEST_TYPE_DIRECTION=USB_REQUEST_TYPE_DIRECTION.DEV_TO_HOST,
                     ):
        dev_req = make_usb_device_request(
            bmRequestType_recipient=bmRequestType_recipient,
            bmRequestType_type=bmRequestType_type,
            bmRequestType_data_transfer_direction=bmRequestType_data_transfer_direction,
            bRequest=bRequest,
            wValue=wValue,
            wIndex=wIndex,
            wLength=wLength)
        # read the device descriptor
        # SETUP STAGE, send request for descriptor downloading
        yield from self.send(UsbPacketToken(USB_PID.TOKEN_SETUP, addr, 0))
        yield from self.send(UsbPacketData(USB_PID.DATA_0, dev_req))
        yield from self.wait_on_ack()

        # DATA stage
        data = yield from self.receive_bulk(addr, 0, USB_PID.DATA_1)
        # STATUS stage
        yield from self.transmit_bulk(addr, 0, USB_PID.DATA_1, [])
        return data

    def control_write(self, addr:int, ep:int, bmRequestType_type:USB_REQUEST_TYPE_TYPE,
                      bRequest:int, wValue:int, wIndex:int, buff:List[int],
                      bmRequestType_recipient:USB_REQUEST_TYPE_RECIPIENT=USB_REQUEST_TYPE_RECIPIENT.DEVICE,
                      bmRequestType_data_transfer_direction:USB_REQUEST_TYPE_DIRECTION=USB_REQUEST_TYPE_DIRECTION.HOST_TO_DEV,
                      ):
        p = UsbPacketToken(USB_PID.TOKEN_SETUP, addr, ep)
        yield from self.send(p)

        dev_req = make_usb_device_request(
            bmRequestType_recipient=bmRequestType_recipient,
            bmRequestType_type=bmRequestType_type,
            bmRequestType_data_transfer_direction=bmRequestType_data_transfer_direction,
            bRequest=bRequest,
            wValue=wValue,
            wIndex=wIndex,
            wLength=len(buff))

        yield from self.send(UsbPacketData(USB_PID.DATA_0, dev_req))
        yield from self.wait_on_ack()
        if buff:
            yield from self.transmit_bulk(addr, 0, USB_PID.DATA_1, buff)
        else:
            # no data present skiping write
            pass

        # STATUS stage
        data = yield from self.receive_bulk(addr, 0, USB_PID.DATA_1)
        assert not data, data

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
        descr = yield from self.receive_bulk(addr, 0, USB_PID.DATA_1)
        # assert len(descr) == int(dev_req_get_descr.wLength), (descriptor_t, wIndex, len(descr), int(dev_req_get_descr.wLength))
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
        new_addr = len(self.descr) + 1
        # init device address
        yield from self.control_write(0, 0,
                                      bmRequestType_type=USB_REQUEST_TYPE_TYPE.STANDARD,
                                      bRequest=USB_REQUEST.SET_ADDRESS,
                                      wValue=new_addr,
                                      wIndex=0,
                                      buff=[])
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
        self._descriptors_downloaded = True
