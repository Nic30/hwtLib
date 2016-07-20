from hdl_toolkit.intfLvl import connect, Unit, Param
from hwtLib.samples.iLvl.simpleAxiStream import SimpleUnitAxiStream
from hdl_toolkit.interfaces.amba import AxiStream

class SimpleSubunit3(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(128)
        
    def _declr(self):
        with self._paramsShared():
            self.subunit0 = SimpleUnitAxiStream() 
            
            with self._asExtern():
                self.a0 = AxiStream()
                self.b0 = AxiStream()
        
    def _impl(self):
        u = self.subunit0
        connect(self.a0, u.a)
        connect(u.b, self.b0)

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(SimpleSubunit3))
