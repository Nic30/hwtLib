from hdl_toolkit.hdlObjects.specialValues import DIRECTION
from hdl_toolkit.synthesizer.interfaceLevel.interface import Interface
from hdl_toolkit.synthesizer.param import Param
from hwtLib.interfaces.amba import AxiStream


class FullDuplexAxiStream(Interface):
    def _config(self):
        self.DATA_WIDTH = Param(64)
    
    def _declr(self):
        with self._paramsShared():
            self.tx = AxiStream()
            self.rx = AxiStream(masterDir=DIRECTION.IN)
