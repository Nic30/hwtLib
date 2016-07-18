from hdl_toolkit.intfLvl import Param, c
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import And
from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.interfaces.utils import addClkRstn
from hwtLib.handshaked.compBase import HandshakedCompBase

class HandshakedFork(HandshakedCompBase):
    """
    Clone input stream to n identical output streams
    transaction is made in all interfaces or none of them
    """
    def _config(self):
        self.OUT_CH = Param(2)
        super()._config()
        
    def _declr(self):
        with self._asExtern(), self._paramsShared():
            addClkRstn(self)
            self.dataIn = self.intCls()
            self.dataOut = self.intCls(multipliedBy=self.OUT_CH)

    def _impl(self):
        rd = self.getRd
        vld = self.getVld
        data = self.getData
        
        for io in self.dataOut:
            for i, o in zip(data(self.dataIn), data(io)):
                c(i, o)
        
        outRd = And(*[rd(i) for i in self.dataOut])
        c(outRd, rd(self.dataIn)) 

        for o in self.dataOut:
            # everyone else is ready and input is valid
            deps = [vld(self.dataIn)]
            for otherO in self.dataOut:
                if otherO is o:
                    continue
                deps.append(rd(otherO))
            _vld = And(*deps)
            
            c(_vld, vld(o))  
        
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = HandshakedFork(Handshaked)
    print(toRtl(u))
