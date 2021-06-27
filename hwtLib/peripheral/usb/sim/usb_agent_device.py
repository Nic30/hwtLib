from typing import Deque, Union, List

from hwtLib.peripheral.usb.constants import USB_PID
from hwtLib.peripheral.usb.descriptors.bundle import UsbDescriptorBundle, \
    UsbNoSuchDescriptor
from hwtLib.peripheral.usb.descriptors.std import USB_DESCRIPTOR_TYPE, \
    usb_descriptor_device_t, usb_descriptor_configuration_t, \
    usb_descriptor_device_qualifier_t, LANG_ID_EN_US
from hwtLib.peripheral.usb.device_request import usb_device_request_t, \
    USB_REQUEST_TYPE_RECIPIENT, USB_REQUEST_TYPE_TYPE, \
    USB_REQUEST_TYPE_DIRECTION, USB_REQUEST
from hwtLib.peripheral.usb.sim.agent_base import UsbAgent, UsbPacketToken, \
    UsbPacketData, UsbPacketHandshake
from pyMathBitPrecise.bit_utils import mask


class UsbDevAgent(UsbAgent):
    """
    This agent uses rx and tx queue to comunicate with a USB device.
    The agnet implements address assignment and descriptor upload and it is
    meant to be extended with a specific functionality of USB device.
    """

    def __init__(self,
                 rx: Deque[Union[UsbPacketToken, UsbPacketData]],
                 tx: Deque[Union[UsbPacketToken, UsbPacketData]],
                 descriptors:UsbDescriptorBundle):
        super(UsbDevAgent, self).__init__(rx, tx)
        # dictionary endp: last data pid value
        self.last_data_pid = {0: USB_PID.DATA_1}
        self.addr = 0
        self.descr = descriptors

    def set_data_pid(self, pid: USB_PID):
        assert self.last_data_pid != pid, (self.last_data_pid, pid, "data pid should change between the transactions")
        self.last_data_pid = pid

    def get_data_pid(self):
        pid = self.last_data_pid
        if pid == USB_PID.DATA_1:
            pid = USB_PID.DATA_0
        else:
            pid = USB_PID.DATA_1
        self.last_data_pid = pid
        return pid

    def send_data(self, endp: int, pid_init: USB_PID, maxPacketLen: int, data_bytes: List[int]):
        pid = pid_init
        begin = 0
        end = len(data_bytes)
        while True:
            t = yield from self.receive(UsbPacketToken)
            assert t.pid == USB_PID.TOKEN_IN, t
            assert t.addr == self.addr, (t, self.addr)
            assert t.endp == endp, t

            _end = min(begin + maxPacketLen, end)
            p = UsbPacketData(pid, data_bytes[begin:_end])
            yield from self.send(p)
            yield from self.wait_on_ack()
            begin = _end
            if pid == USB_PID.DATA_0:
                pid = USB_PID.DATA_1
            elif pid == USB_PID.DATA_1:
                pid = USB_PID.DATA_0
            else:
                raise ValueError()

            if len(p.data) < maxPacketLen:
                break

    def proc(self):
        while True:
            # wait on request from host
            t = yield from self.receive(UsbPacketToken)
            assert t.pid == USB_PID.TOKEN_SETUP, t
            assert t.addr == self.addr, t
            assert t.endp == 0, t
            req = yield from self.receive(UsbPacketData)
            assert req.pid == USB_PID.DATA_0, req
            req = req.unpack(usb_device_request_t)
            yield from self.send_ack()

            # process setup request
            if int(req.bmRequestType.recipient) == USB_REQUEST_TYPE_RECIPIENT.DEVICE and\
               int(req.bmRequestType.type) == USB_REQUEST_TYPE_TYPE.STANDARD:
                if int(req.bmRequestType.data_transfer_direction) == USB_REQUEST_TYPE_DIRECTION.DEV_TO_HOST:
                    # now we expect that we get TOKEN_IN so the device can send the data to host
                    if int(req.bRequest) == USB_REQUEST.GET_DESCRIPTOR:
                        _v = int(req.wValue)
                        des_t = _v >> 8
                        des_i = _v & mask(8)
                        lang_id = int(req.wIndex)
                        wLength = int(req.wLength)

                        if des_t == USB_DESCRIPTOR_TYPE.DEVICE:
                            descr_t = usb_descriptor_device_t
                        elif des_t == USB_DESCRIPTOR_TYPE.CONFIGURATION:
                            descr_t = usb_descriptor_configuration_t
                        elif des_t == USB_DESCRIPTOR_TYPE.DEVICE_QUALIFIER:
                            descr_t = usb_descriptor_device_qualifier_t
                        elif des_t == USB_DESCRIPTOR_TYPE.STRING:
                            descr_t = str
                            if des_i == 0:
                                assert lang_id == 0, lang_id
                            elif lang_id != LANG_ID_EN_US:
                                raise NotImplementedError("Need to filter string descriptors for this specific "
                                                          "language or language id is invalid", lang_id)
                        else:
                            raise NotImplementedError(des_t)

                        try:
                            descr_i = self.descr.get_descriptor_index(descr_t, des_i)
                        except UsbNoSuchDescriptor:
                            descr_i = None

                        if descr_i is None:
                            t = yield from self.receive(UsbPacketToken)
                            assert t.pid == USB_PID.TOKEN_IN, t
                            assert t.addr == self.addr, (t, self.addr)
                            assert t.endp == 0, t
                            yield from self.send(UsbPacketHandshake(USB_PID.HS_STALL))
                            continue
                        else:
                            dev_descr = self.descr.get_descriptor(usb_descriptor_device_t, 0)[1]
                            ep0_max_packet_size = int(dev_descr.body.bMaxPacketSize)
                            data = self.descr.get_descr_bytes(descr_i, wLength)
                            yield from self.send_data(0, USB_PID.DATA_1, ep0_max_packet_size, data)
                    else:
                        raise NotImplementedError()

                    t = yield from self.receive(UsbPacketToken)
                    assert t.pid == USB_PID.TOKEN_OUT, t
                    assert t.addr == self.addr, (t, self.addr)
                    assert t.endp == 0, t

                    t = yield from self.receive(UsbPacketData)
                    assert t.pid == USB_PID.DATA_1, t
                    assert len(t.data) == 0, t
                    yield from self.send_ack()
                else:
                    _addr = self.addr
                    # host to dev
                    if int(req.bRequest) == USB_REQUEST.SET_ADDRESS:
                        assert int(req.wIndex) == 0, req.wIndex
                        assert int(req.wLength) == 0, req.wLength
                        addr = int(req.wValue)
                        assert addr > 0, addr
                        self.addr = addr
                    else:
                        raise NotImplementedError(req)

                    t = yield from self.receive(UsbPacketToken)
                    assert t.pid == USB_PID.TOKEN_IN, t
                    assert t.addr == _addr, (t, _addr)  # intentionaly use old address
                    assert t.endp == 0, t
                    yield from self.send(UsbPacketData(USB_PID.DATA_1, []))
                    yield from self.wait_on_ack()
            else:
                raise NotImplementedError(req)

