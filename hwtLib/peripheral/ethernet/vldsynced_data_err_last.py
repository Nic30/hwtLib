from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from hwt.interfaces.std import Signal, VldSynced, VectSignal


class VldSyncedDataErrLast(VldSynced):
    """
    Interface with data, vld, err, last signal

    .. hwt-autodoc::
    """

    def _declr(self):
        VldSynced._declr(self)
        if self.DATA_WIDTH > 8:
            self.mask = VectSignal(self.DATA_WIDTH // 8)
        self.err = Signal()
        self.last = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = VldSyncedDataErrLastAgent(sim, self)


class VldSyncedDataErrLastAgent(VldSyncedAgent):

    def __init__(self, sim: HdlSimulator, intf, allowNoReset=False):
        VldSyncedAgent.__init__(self, sim, intf, allowNoReset=allowNoReset)
        self.has_mask = hasattr(intf, "mask")

    def get_data(self):
        i = self.intf
        if self.has_mask:
            return (i.data.read(), i.mask.read(), i.err.read(), i.last.read())
        else:
            return (i.data.read(), i.err.read(), i.last.read())

    def set_data(self, data):
        i = self.intf
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
