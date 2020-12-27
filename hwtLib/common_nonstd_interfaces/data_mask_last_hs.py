from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, Signal, Handshaked
from hwt.synthesizer.param import Param
from hwtSimApi.hdlSimulator import HdlSimulator


class DataMaskLastHs(Handshaked):
    """
    Handshaked interface with data, mask, last signal.

    .. hwt-autodoc::
    """
    def _config(self):
        self.MASK_GRANULARITY = Param(8)
        Handshaked._config(self)

    def _declr(self):
        super(DataMaskLastHs, self)._declr()
        assert self.DATA_WIDTH % self.MASK_GRANULARITY == 0, (
            self.DATA_WIDTH, self.MASK_GRANULARITY)
        self.USE_MASK = self.MASK_GRANULARITY != self.DATA_WIDTH
        if self.USE_MASK:
            self.mask = VectSignal(self.DATA_WIDTH // self.MASK_GRANULARITY)
        self.last = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = DataMaskHsAgent(sim, self)


class DataMaskHsAgent(HandshakedAgent):
    """
    Simulation agent for :class:`.DataMaskLastHs` interface.
    """

    def set_data(self, data):
        i = self.intf
        if data is None:
            d, m, last = None, None, None
        else:
            d, m, last = data

        i.mask.write(m)
        i.data.write(d)
        i.last.write(last)

    def get_data(self):
        i = self.intf
        return i.data.read(), i.mask.read(), i.last.read()
