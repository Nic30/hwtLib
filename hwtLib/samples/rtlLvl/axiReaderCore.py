
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.serializer.formater import formatVhdl
from hdl_toolkit.synthesizer.codeOps import connect, If
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist


w = connect


def axiReaderCore():
    n = RtlNetlist("AxiReaderCore")
    rSt_t = Enum('rSt_t', ['rdIdle', 'rdData'])
    
    rSt = n.sig('rSt', rSt_t)
    arRd = n.sig('arRd')
    arVld = n.sig('arVld')
    rVld = n.sig('rVld')
    rRd = n.sig('rRd')

    # ar fsm next
    If(arRd,
       # rdIdle
        If(arVld,
           w(rSt_t.rdData, rSt) 
        ).Else(
           w(rSt_t.rdIdle, rSt)
        )
    ).Else(
        # rdData
        If(rRd & rVld,
           w(rSt_t.rdIdle, rSt)
        ).Else(
           w(rSt_t.rdData, rSt) 
        )
    )
    
    return n, [rSt, arRd, arVld, rVld, rRd]
    
if __name__ == "__main__":
    n, interf = axiReaderCore()
    
    for o in n.synthesize(interf):
            print(formatVhdl(str(o)))
