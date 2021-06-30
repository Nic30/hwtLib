from asyncio.tasks import sleep
from collections import deque
from typing import Tuple, Callable, Union

from hwt.synthesizer.rtlLevel.constants import NOT_SPECIFIED
from hwtLib.peripheral.usb.constants import USB_VER, USB_PID
from hwtLib.peripheral.usb.descriptors.bundle import UsbDescriptorBundle, \
    UsbNoSuchDescriptor
from hwtLib.peripheral.usb.descriptors.std import usb_descriptor_configuration_t, \
    usb_descriptor_interface_t, USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE, \
    USB_ENDPOINT_DIR
from hwtLib.peripheral.usb.device_request import \
    USB_REQUEST_TYPE_RECIPIENT, USB_REQUEST_TYPE_DIRECTION, \
    USB_REQUEST_TYPE_TYPE
from hwtSimApi.process_utils import CallbackLoop, ExitCallbackLoop
from hwtSimApi.simCalendar import DONE


class USBIPPending:

    def __init__(self, seqnum, device, xfer):
        self.seqnum = seqnum
        self.device = device
        self.xfer = xfer


class USBIPOperationPromise():

    def __init__(self, operation_process, sim, clk):
        self.data = NOT_SPECIFIED
        self.operation_process = operation_process(self)
        self.sim = sim

        self.cb = CallbackLoop(
            sim, clk,
            self._pool_process,
            self._continue_with_clk_triggering)

    def _continue_with_clk_triggering(self):
        if self.data is not NOT_SPECIFIED:
            raise ExitCallbackLoop()
        return True

    def schedule(self):
        sim = self.sim
        # [todo] potentialy not thread safe
        # print("Try to schedule")
        # next_time = 0  # sim._events._list[1]
        cb = self.cb()
        with sim.scheduler_lock:
            while sim._current_time_slot is None or sim._current_time_slot.timeslot_end is not DONE:
                pass
            # sim._current_event_list.append(cb)
            next_time = sim._events._list[0] + 2
            sim._schedule_proc(next_time, cb)
            # print("schedule done")

    def _pool_process(self):
        try:
            next(self.operation_process)
        except StopIteration:
            assert self.data is not NOT_SPECIFIED

    def fulfill(self, data):
        self.data = data

    async def pool_sleep_until_fulfil(self, t):
        while self.data is NOT_SPECIFIED:
            await sleep(t)
        return self.data


class USBIPSimDevice():
    """
    :attention: API of this component should be same as the device from library usb1 if possible
        because we want to just swap the device object in sim and test the real device as well
    """

    def __init__(self, usb_agent, addr:int, descriptors:UsbDescriptorBundle):
        self.usb_agent = usb_agent
        self.addr = addr
        self.endp_next_pid = {}
        self.descriptors = descriptors

    def getBusNumber(self):
        return 0

    def getDeviceAddress(self):
        return self.addr

    def getDeviceSpeed(self):
        v = int(self.descriptors[0].body.bcdUSB)
        return USB_VER.from_uint16_t(v)

    def getVendorID(self):
        return int(self.descriptors[0].body.idVendor)

    def getProductID(self):
        return int(self.descriptors[0].body.idProduct)

    def getbcdDevice(self):
        return int(self.descriptors[0].body.bcdDevice)

    def getDeviceClass(self):
        return int(self.descriptors[0].body.bDeviceClass)

    def getDeviceSubClass(self):
        return int(self.descriptors[0].body.bDeviceSubClass)

    def getDeviceProtocol(self):
        return int(self.descriptors[0].body.bDeviceProtocol)

    def getNumConfigurations(self):
        return int(self.descriptors[0].body.bNumConfigurations)

    def iterConfigurations(self):
        descr_i = 0

        while True:
            try:
                d = self.descriptors.get_descriptor(usb_descriptor_configuration_t, descr_i)
            except UsbNoSuchDescriptor:
                break
            yield USBIPSimDeviceConfiguration(self, d[1])
            descr_i += 1

    def open(self):
        return self

    def close(self):
        pass

    def getDevice(self):
        return self

    async def controlRead(self, bmRequestType_recipient:USB_REQUEST_TYPE_RECIPIENT,
                           bmRequestType_type:USB_REQUEST_TYPE_TYPE,
                           bmRequestType_data_transfer_direction:USB_REQUEST_TYPE_DIRECTION,
                           bRequest, wValue, wIndex, wLength):

        def execute_control_read(read_op):
            # print("controlRead", self.addr, bmRequestType_recipient, bmRequestType_type, bmRequestType_data_transfer_direction, bRequest, wValue, wIndex, wLength)
            read_data = yield from self.usb_agent.usb_driver.control_read(
                self.addr, bmRequestType_type, bRequest, wValue, wIndex, wLength,
                bmRequestType_recipient=bmRequestType_recipient,
                bmRequestType_data_transfer_direction=bmRequestType_data_transfer_direction)
            # print("controlRead-done", read_data)
            read_op.fulfill(read_data)

        read_op = USBIPOperationPromise(execute_control_read, self.usb_agent.sim, self.usb_agent.clk)
        read_op.schedule()
        d = await read_op.pool_sleep_until_fulfil(0.01)
        return bytes(d)

    async def controlWrite(self, bmRequestType_recipient:USB_REQUEST_TYPE_RECIPIENT,
                           bmRequestType_type:USB_REQUEST_TYPE_TYPE,
                           bmRequestType_data_transfer_direction:USB_REQUEST_TYPE_DIRECTION,
                           bRequest: int, wValue: int, wIndex: int, data):
        """
        :return: The number of bytes actually sent.
        """

        def execute_control_write(write_op):
            # print("controlWrite", self.addr, bRequestType, bRequest, wValue, wIndex, data)
            yield from self.usb_agent.usb_driver.control_write(
                self.addr, 0, bmRequestType_type, bRequest, wValue, wIndex, data,
                bmRequestType_recipient=bmRequestType_recipient,
                bmRequestType_data_transfer_direction=bmRequestType_data_transfer_direction)
            write_op.fulfill(True)

        write_op = USBIPOperationPromise(execute_control_write, self.usb_agent.sim, self.usb_agent.clk)
        write_op.schedule()
        await write_op.pool_sleep_until_fulfil(0.01)

        return len(data)

    def getTransfer(self):
        return USBIPTransfer(self)


class LIBUSB_TRANSFER_STATUS:
    # Transfer completed without error. Note that this does not indicate
    # that the entire amount of requested data was transferred.
    TRANSFER_COMPLETED = 0
    # Transfer failed
    TRANSFER_ERROR = 1
    # Transfer timed out
    TRANSFER_TIMED_OUT = 2
    # Transfer was cancelled
    TRANSFER_CANCELLED = 3
    # For bulk/interrupt endpoints: halt condition detected (endpoint
    # stalled). For control endpoints: control request not supported.
    TRANSFER_STALL = 4
    # Device was disconnected
    TRANSFER_NO_DEVICE = 5
    # Device sent more data than requested
    TRANSFER_OVERFLOW = 6


class USBIPTransfer():

    def __init__(self, dev: USBIPSimDevice):
        self.dev = dev
        self.is_in = None
        self.transfer_t = None
        self.ep = None
        self.buffer = None
        self.len = None
        self.callback = None

    def setBulk(self, ep:int, buff_or_len:Union[int, bytes], callback:Callable[['USBIPTransfer'], None]):
        self.is_in = ep >= 0x80
        self.ep = ep & ~0x80
        self.transfer_t = USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.BULK
        if self.is_in:
            assert isinstance(buff_or_len, int), buff_or_len
            self.len = buff_or_len
        else:
            assert isinstance(buff_or_len, (list, tuple, bytes, deque))
            self.buffer = buff_or_len
        self.callback = callback

    def _next_bulk_pid(self, pid):
        if pid == USB_PID.DATA_0:
            return USB_PID.DATA_1
        elif pid == USB_PID.DATA_1:
            return USB_PID.DATA_0
        else:
            raise NotImplementedError(pid)

    async def submit(self):
        if self.transfer_t == USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.BULK:
            if self.is_in:

                def execute_bulk(read_op):
                    # print("IN", self.dev.addr, self.ep)
                    epk = (self.ep, USB_ENDPOINT_DIR.IN)
                    pid = self.dev.endp_next_pid.setdefault(epk, USB_PID.DATA_0)
                    read_data = yield from self.dev.usb_agent.usb_driver.receive_bulk(
                        self.dev.addr, self.ep, pid, 512)
                    # print("IN-done", read_data)
                    if read_data is None:
                        read_data = []  # nack, do not update data pid
                    else:
                        self.dev.endp_next_pid[epk] = self._next_bulk_pid(pid)

                    read_op.fulfill(read_data)

            else:

                def execute_bulk(read_op):
                    # print("OUT", self.dev.addr, self.ep, self.buffer)
                    epk = (self.ep, USB_ENDPOINT_DIR.OUT)
                    pid = self.dev.endp_next_pid.setdefault(epk, USB_PID.DATA_0)
                    yield from self.dev.usb_agent.usb_driver.transmit_bulk(
                        self.dev.addr, self.ep, pid, self.buffer)
                    # print("OUT-done")
                    self.dev.endp_next_pid[epk] = self._next_bulk_pid(pid)
                    read_op.fulfill(None)

            op = USBIPOperationPromise(execute_bulk, self.dev.usb_agent.sim, self.dev.usb_agent.clk)
            op.schedule()
            buffer = await op.pool_sleep_until_fulfil(0.01)
            if self.is_in and buffer is not None:
                self.buffer = list(buffer)
            self.callback(self)
        else:
            raise NotImplementedError()

    def getBuffer(self):
        return self.buffer

    def getActualLength(self):
        return len(self.buffer)

    def getStatus(self):
        return LIBUSB_TRANSFER_STATUS.TRANSFER_COMPLETED


class USBIPDevice:

    def __init__(self, devid: Tuple[int, int], hnd: USBIPSimDevice):
        self.devid = devid
        self.hnd = hnd

    def packDevid(self):
        # dev.getBusNumber() << 16 | dev.getDeviceAddress()
        did = self.devid
        return (did[0] << 16 | did[1])


class USBIPSimDeviceConfiguration():

    def __init__(self, dev: USBIPSimDevice, config_descr:usb_descriptor_configuration_t):
        self.dev = dev
        self.config_descr = config_descr

    def getConfigurationValue(self):
        return 1

    def getNumInterfaces(self):
        return int(self.config_descr.body.bNumInterfaces)

    def iterInterfaces(self):
        descr_i = 0

        while True:
            try:
                d = self.dev.descriptors.get_descriptor(usb_descriptor_interface_t, descr_i)
            except UsbNoSuchDescriptor:
                break
            yield USBIPSimDeviceInterface(self, d[1])
            descr_i += 1


class USBIPSimDeviceInterface():

    def __init__(self, conf: USBIPSimDeviceConfiguration, descr: usb_descriptor_interface_t):
        self.conf = conf
        self.descr = descr

    def iterSettings(self):
        yield USBIPSimDeviceInterfaceSetting(self)


class USBIPSimDeviceInterfaceSetting():

    def __init__(self, intf: USBIPSimDeviceInterface):
        self.intf = intf

    def getClass(self):
        return int(self.intf.descr.body.bInterfaceClass)

    def getSubClass(self):
        return int(self.intf.descr.body.bInterfaceSubClass)

    def getProtocol(self):
        return int(self.intf.descr.body.bInterfaceProtocol)
