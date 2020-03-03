from hwt.hdl.constants import DIRECTION
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream


class AxiStreamFullDuplex(Interface):

    def _config(self):
        AxiStream._config(self)
        self.HAS_RX = Param(True)
        self.HAS_TX = Param(True)

    def _declr(self):
        with self._paramsShared():
            if self.HAS_TX:
                self.tx = AxiStream()

            if self.HAS_RX:
                self.rx = AxiStream(masterDir=DIRECTION.IN)
