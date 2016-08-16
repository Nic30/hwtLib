from hdl_toolkit.interfaces.amba import AxiStream_withoutSTRB
from hwtLib.axi.axis_compBase import AxiSCompBase
from hwtLib.handshaked.reg2 import HandshakedReg2
from hwtLib.axi.axis_reg import AxiSReg


class AxiSReg2(AxiSCompBase, HandshakedReg2):
    """
    Register for axi stream interface
    
    LATENCY=2
    DELAY=1
    """
    regCls = AxiSReg
    pass
    
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = AxiSReg2(AxiStream_withoutSTRB)
    
    print(toRtl(u))
