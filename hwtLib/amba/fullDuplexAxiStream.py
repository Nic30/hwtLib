from hwt.hdl.constants import DIRECTION
from hwt.synthesizer.interface import Interface
from hwtLib.amba.axis import AxiStream


class FullDuplexAxiStream(Interface):

    def _config(self):
        AxiStream._config(self)

    def _declr(self):
        with self._paramsShared():
            self.tx = AxiStream()
            self.rx = AxiStream(masterDir=DIRECTION.IN)
