from hwt.hdl.types.bits import Bits
from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from hwt.interfaces.std import VldSynced, Signal
from hwt.synthesizer.param import Param
from hwtLib.peripheral.usb.constants import usb_pid_t, usb_frame_number_t, \
    USB_PID
from hwtSimApi.hdlSimulator import HdlSimulator


class DataErrVldKeepLast(VldSynced):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        VldSynced._config(self)
        self.USE_KEEP: bool = Param(True)

    def _declr(self):
        VldSynced._declr(self)
        if self.USE_KEEP:
            self.keep = Signal(Bits(self.DATA_WIDTH // 8))
        self.error = Signal()
        self.last = Signal()

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = DataErrVldKeepLastAgent(sim, self)


class DataErrVldKeepLastAgent(VldSyncedAgent):
    """
    A simulation agent for :class:`~.DataErrVldKeepLast` interface.
    """

    def set_data(self, data):
        i = self.intf
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

    def get_data(self):
        i = self.intf
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


class Usb2SieRxOut(VldSynced):
    """
    :note: address in not important because it is checked with current_usb_addr
       it is only important if this is the address of this device
    :attention: validity of the endp/frame_number depens on pid value

    .. hwt-autodoc::
    """

    def _config(self):
        pass

    def _declr(self):
        self.pid = Signal(usb_pid_t)
        self.endp = Signal(usb_pid_t)
        self.frame_number = Signal(usb_frame_number_t)
        self.error = Signal()  # pid error or crc5 error or invalid address or missing/extra data
        self.vld = Signal()

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = Usb2SieRxOutAgent(sim, self)


class Usb2SieRxOutAgent(VldSyncedAgent):
    """
    A simulation agent for :class:`~.Usb2SieRxOut` interface.
    """
    def set_data(self, data):
        if data is None:
            data = None, None, None, None
        pid, endp, frame_number, error = data
        i = self.intf
        i.pid.write(pid)
        i.endp.write(endp)
        i.frame_number.write(frame_number if pid == USB_PID.TOKEN_SOF else None)
        i.error.write(error)

    def get_data(self):
        i = self.intf

        return (
            i.pid.read(),
            i.endp.read(),
            i.frame_number.read(),
            i.error.read(),
        )
