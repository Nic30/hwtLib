from hwt.hwIOs.agents.vldSync import HwIODataVldAgent
from hwt.hwIOs.std import HwIOSignal, HwIODataVld, HwIOVectSignal
from hwt.pyUtils.typingFuture import override
from hwtSimApi.hdlSimulator import HdlSimulator


class VldSyncedDataErrLast(HwIODataVld):
    """
    Interface with data, vld, err, last signal

    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        HwIODataVld.hwDeclr(self)
        if self.DATA_WIDTH > 8:
            self.mask = HwIOVectSignal(self.DATA_WIDTH // 8)
        self.err = HwIOSignal()
        self.last = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = VldSyncedDataErrLastAgent(sim, self)


class VldSyncedDataErrLastAgent(HwIODataVldAgent):

    def __init__(self, sim: HdlSimulator, hwIO, allowNoReset=False):
        HwIODataVldAgent.__init__(self, sim, hwIO, allowNoReset=allowNoReset)
        self.has_mask = hasattr(hwIO, "mask")

    @override
    def get_data(self):
        i = self.hwIO
        if self.has_mask:
            return (i.data.read(), i.mask.read(), i.err.read(), i.last.read())
        else:
            return (i.data.read(), i.err.read(), i.last.read())

    @override
    def set_data(self, data):
        i = self.hwIO
        if self.has_mask:
            if data is None:
                data = (None, None, None, None)
            d, m, e, last = data
            i.mask.write(m)
        else:
            if data is None:
                data = (None, None, None)
            d, e, last = data
        i.data.write(d)
        i.err.write(e)
        i.last.write(last)
