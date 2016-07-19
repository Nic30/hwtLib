from hwtLib.axi.axis_compBase import AxiSCompBase 
from hwtLib.handshaked.fork import HandshakedFork

class AxiSFork(AxiSCompBase, HandshakedFork):
    pass
            
        
if __name__ == "__main__":
    from hdl_toolkit.interfaces.amba import AxiStream
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = AxiSFork(AxiStream)
    print(toRtl(u))