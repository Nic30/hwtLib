from hwt.hdl.types.bits import HBits
from hwt.hwIOs.agents.vldSync import HwIODataVldAgent
from hwt.hwIOs.std import HwIODataVld, HwIOSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.peripheral.usb.constants import usb_pid_t, usb_frame_number_t, \
    USB_PID
from hwtSimApi.hdlSimulator import HdlSimulator


class DataErrVldKeepLast(HwIODataVld):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        HwIODataVld.hwConfig(self)
        self.USE_KEEP: bool = HwParam(True)

    @override
    def hwDeclr(self):
        HwIODataVld.hwDeclr(self)
        if self.USE_KEEP:
            self.keep = HwIOSignal(HBits(self.DATA_WIDTH // 8))
        self.error = HwIOSignal()
        self.last = HwIOSignal()

    @override
    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = DataErrVldKeepLastAgent(sim, self)


class DataErrVldKeepLastAgent(HwIODataVldAgent):
    """
    A simulation agent for :class:`~.DataErrVldKeepLast` interface.
    """

    @override
    def set_data(self, data):
        i = self.hwIO
        if i.USE_KEEP:
            if data is None:
                data = None, None, None, None
            data, keep, error, last = data
            i.keep.write(keep)
        else:
            if data is None:
                data = None, None, None
            data, error, last = data
        i.data.write(data)
        i.error.write(error)
        i.last.write(last)

    @override
    def get_data(self):
        i = self.hwIO
        if i.USE_KEEP:
            return (
                i.data.read(),
                i.keep.read(),
                i.error.read(),
                i.last.read(),
            )
        else:
            return (
                i.data.read(),
                i.error.read(),
                i.last.read(),
            )


class Usb2SieRxOut(HwIODataVld):
    """
    :note: address in not important because it is checked with current_usb_addr
       it is only important if this is the address of this device
    :attention: validity of the endp/frame_number depens on pid value

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        pass

    @override
    def hwDeclr(self):
        self.pid = HwIOSignal(usb_pid_t)
        self.endp = HwIOSignal(usb_pid_t)
        self.frame_number = HwIOSignal(usb_frame_number_t)
        self.error = HwIOSignal()  # pid error or crc5 error or invalid address or missing/extra data
        self.vld = HwIOSignal()

    @override
    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = Usb2SieRxOutAgent(sim, self)


class Usb2SieRxOutAgent(HwIODataVldAgent):
    """
    A simulation agent for :class:`~.Usb2SieRxOut` interface.
    """
    @override
    def set_data(self, data):
        if data is None:
            data = None, None, None, None
        pid, endp, frame_number, error = data
        i = self.hwIO
        i.pid.write(pid)
        i.endp.write(endp)
        i.frame_number.write(frame_number if pid == USB_PID.TOKEN_SOF else None)
        i.error.write(error)

    @override
    def get_data(self):
        i = self.hwIO

        return (
            i.pid.read(),
            i.endp.read(),
            i.frame_number.read(),
            i.error.read(),
        )
