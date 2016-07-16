from hdl_toolkit.intfLvl import connect, Param, Unit
from hdl_toolkit.interfaces.amba import AxiStream
from hwtLib.samples.iLvl.simple2withNonDirectIntConnection import Simple2withNonDirectIntConnection

class UnitToUnitConnection(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        with self._paramsShared():
            with self._asExtern():
                self.a = AxiStream()
                self.b = AxiStream()
    
            self.u0 = Simple2withNonDirectIntConnection()
            self.u1 = Simple2withNonDirectIntConnection()
        
    def _impl(self):
        connect(self.a, self.u0.a)
        connect(self.u0.c, self.u1.a)
        connect(self.u1.c, self.b)
    
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(UnitToUnitConnection) )
