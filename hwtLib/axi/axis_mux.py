from hwtLib.axi.axis_compBase import AxiSCompBase 
from hwtLib.handshaked.mux import HandshakedMux


class AxiSMux(AxiSCompBase, HandshakedMux):
    pass
            

#class AxiSMuxContainer(Unit):
#    """
#    Test container
#    """
#    def _declr(self):
#        with self._asExtern():
#            self.dataIn = AxiStream()
#            self.dataOut0 = AxiStream()
#            self.dataOut1 = AxiStream()
#            self.dataOut2 = AxiStream()
#            self.sel = Signal(dtype=vecT(2))
#    
#        self.mux = AxiStreamMux()
#    
#    def _impl(self):
#        m = self.mux
#        c(self.dataIn, m.dataIn)
#        c(m.dataOut[0], self.dataOut0)
#        c(m.dataOut[1], self.dataOut1)
#        c(m.dataOut[2], self.dataOut2)
#        
if __name__ == "__main__":
    from hwtLib.interfaces.amba import AxiStream
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = AxiSMux(AxiStream)
    print(toRtl(u))