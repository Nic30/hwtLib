from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.synthesizer.codeOps import If, connect
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param
from hdl_toolkit.synthesizer.shortcuts import toRtl
from hwtLib.interfaces.amba import AxiStream

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
