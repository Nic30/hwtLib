from hdl_toolkit.intfLvl import connect, Param, Unit
from hdl_toolkit.interfaces.amba import AxiStream


class SimpleUnitAxiStream(Unit):
    #def _config(self):
    #    self.DATA_WIDTH = Param(8)

    def _declr(self):
        with self._asExtern():
            self.a = AxiStream()
            self.b = AxiStream()
        #self._shareAllParams()
        
    def _impl(self):
        connect(self.a, self.b)

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(SimpleUnitAxiStream))
