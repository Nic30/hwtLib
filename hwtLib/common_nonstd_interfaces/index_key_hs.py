from typing import Union, Tuple

from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, HandshakeSync, VectSignal
from hwt.synthesizer.param import Param
from pycocotb.hdlSimulator import HdlSimulator


class IndexKeyHs(Handshaked):

    def _config(self):
        self.INDEX_WIDTH = Param(4)
        self.KEY_WIDTH = Param(4)

    def _declr(self):
        HandshakeSync._declr(self)
        if self.KEY_WIDTH:
            self.key = VectSignal(self.KEY_WIDTH)
        self.index = VectSignal(self.INDEX_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = IndexKeyHsAgent(sim, self)


class IndexKeyHsAgent(HandshakedAgent):

    def get_data(self) -> Union[Tuple[int, int], int]:
        i = self.intf
        if i.KEY_WIDTH:
            return (i.key.read(), i.index.read())
        else:
            return i.index.read()

    def set_data(self, data: Union[Tuple[int, int], int]):
        intf = self.intf
        if intf.KEY_WIDTH:
            if data is None:
                k = None
                i = None
            else:
                k, i = data
            intf.key.write(k)
        else:
            i = data
        intf.index.write(i)

