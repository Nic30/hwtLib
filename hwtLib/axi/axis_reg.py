from hdl_toolkit.interfaces.amba import AxiStream_withoutSTRB
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.axi.axis_compBase import AxiSCompBase

class AxiSReg(AxiSCompBase, HandshakedReg):
    """
    Register for axi stream interface
    """
    pass
    
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = AxiSReg(AxiStream_withoutSTRB)
    
    print(toRtl(u))
