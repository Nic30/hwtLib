from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from pycocotb.hdlSimulator import HdlSimulator
from hwt.interfaces.std import Signal, VldSynced


class VldSyncedDataErrLast(VldSynced):
    """
    Interface with data, vld, err, last signal
    """
    def _declr(self):
        VldSynced._declr(self)
        self.err = Signal()
        self.last = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = VldSyncedDataErrLastAgent(sim, self)


class VldSyncedDataErrLastAgent(VldSyncedAgent):

    def get_data(self):
        i = self.intf
        return (i.data.read(), i.err.read(), i.last.read())

    def set_data(self, data):
        if data is None:
            data = (None, None, None)
        d, e, last = data
        i = self.intf
        i.data.write(d)
        i.err.write(e)
        i.last.write(last)
