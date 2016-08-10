from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.interfaces.std import s
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.synthesizer.codeOps import Switch, If, c
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit


class AxiSsof(Unit):
    """
    Start of frame detector for axi stream
    """
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            
            self.ready = s()
            self.valid = s()
            self.last = s()
            self.sof = s()
        
    def listenOn(self, axi, dstReady):
        c(dstReady, self.ready)
        c(axi.valid, self.valid)
        c(axi.last, self.last)
        

    def _impl(self):
        stT = Enum("stT", ["stSof", 'stIdle'])
        st = self._reg("st", stT, stT.stSof)
        
        # next state logic
        Switch(st)\
        .Case(stT.stSof,
                If(self.valid & self.ready & ~self.last,
                   c(stT.stIdle, st)
                ).Else(
                   c(st, st)
                )
        ).Case(stT.stIdle,
                If(self.valid & self.ready & self.last,
                   c(stT.stSof, st)
                ).Else(
                   c(st, st)
                )
        )
                
        c(st._eq(stT.stSof), self.sof)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = AxiSsof()
    print(toRtl(u))