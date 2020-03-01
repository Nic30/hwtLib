from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from hwt.interfaces.std import VectSignal, VldSynced
from hwt.synthesizer.param import Param
from pycocotb.hdlSimulator import HdlSimulator


class DataMaskVld(VldSynced):
    """
    Simple interface with data, mask and vld signal
    """
    def _config(self):
        self.MASK_GRANULARITY = Param(8)
        VldSynced._config(self)

    def _declr(self):
        super(DataMaskVld, self)._declr()
        assert self.DATA_WIDTH % self.MASK_GRANULARITY == 0, (
            self.DATA_WIDTH, self.MASK_GRANULARITY)
        self.mask = VectSignal(self.DATA_WIDTH // self.MASK_GRANULARITY)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = DataMaskVldAgent(sim, self)


class DataMaskVldAgent(VldSyncedAgent):

    def set_data(self, data):
        i = self.intf
        if data is None:
            d, m = None, None
        else:
            d, m = data

        i.mask.write(m)
        i.data.write(d)

    def get_data(self):
        i = self.intf
        return i.data.read(), i.mask.read()

