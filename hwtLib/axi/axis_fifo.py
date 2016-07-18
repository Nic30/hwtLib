from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.axi.axis_compBase import AxiSCompBase


class AxiSFifo(AxiSCompBase, HandshakedFifo):
    """
    Synchronous fifo for axi-stream interface. 
    """
    pass
            
if __name__ == "__main__":
    from hdl_toolkit.interfaces.amba import AxiStream_withoutSTRB
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    
    u = AxiSFifo(AxiStream_withoutSTRB)
    u.DEPTH.set(4)
    
    print(toRtl(u))    
            
            
            
