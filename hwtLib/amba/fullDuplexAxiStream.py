from hwt.hdlObjects.constants import DIRECTION
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream


class FullDuplexAxiStream(Interface):
    def _config(self):
        self.DATA_WIDTH = Param(64)
    
    def _declr(self):
        with self._paramsShared():
            self.tx = AxiStream()
            self.rx = AxiStream(masterDir=DIRECTION.IN)
