
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.serializer.vhdlFormater import formatVhdl
from hdl_toolkit.synthesizer.codeOps import connect, If
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist


w = connect


def LeadingZero():
    t = vecT(64)
    resT = vecT(8)
    n = RtlNetlist("LeadingZero")
    
    s_in = n.sig("s_in", t)
    index = n.sig("s_indexOfFirstZero", resT)
    
    leadingZeroTop = None  # index is index of first empty record or last one
    for i in reversed(range(8)):
        connections = w(i, index)
        if leadingZeroTop is None:
            leadingZeroTop = connections 
        else:
            leadingZeroTop = If(s_in[i]._eq(0),
               connections
            ).Else(
               leadingZeroTop
            )    
    
    interf = [s_in, index]
    
    return n, interf

if __name__ == "__main__":
    n, interf = LeadingZero()
    
    for o in n.synthesize(interf):
            print(formatVhdl(str(o)))

