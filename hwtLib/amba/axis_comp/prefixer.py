from hwt.interfaces.utils import addClkRstn
from hwt.code import If, connect
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.shortcuts import toRtl
from hwtLib.amba.axis import AxiStream

class AxiSPrefixer(Unit):
    """
    Prepend frame from prefix to every frame on data channel
    result is merged into one frame
    """
    def _config(self):
        self.DATA_WIDTH = Param(64)
        
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream()
            self.dataOut = AxiStream()
            self.prefix = AxiStream()
    
    def _impl(self):
        prefixAdded = self._reg("prefixAdded", defVal=False)
        
        inVld = self.dataIn.valid
        outRd = self.dataOut.ready
        last = self.dataIn.last
        
        isLast = inVld & outRd & last
        
        If(prefixAdded,
            self.dataOut ** self.dataIn,
            If(isLast,
               prefixAdded ** False 
            )
        ).Else(
           connect(self.prefix, self.dataOut, exclude=[self.prefix.last]),
           self.dataOut.last ** False,
           prefixAdded ** (self.prefix.valid & self.prefix.last & outRd),
           self.dataIn.ready ** False           
        )

        
if __name__ == "__main__":
    u = AxiSPrefixer()
    print(toRtl(u))
