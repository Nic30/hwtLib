
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.serializer.formater import formatVhdl
from hdl_toolkit.synthesizer.codeOps import  If
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist

def Counter():
    t = vecT(8)
    n = RtlNetlist("LeadingZero")
    
    en = n.sig("en")
    rst = n.sig("rst")
    clk = n.sig("clk")
    s_out = n.sig("s_out", t)
    cnt = n.sig("cnt", t, clk=clk, syncRst=rst, defVal=0)
    
    If(en,
       cnt ** (cnt + 1)
    ).Else(
       cnt._same()
    )
    
    s_out ** cnt
    
    interf = [rst, clk, s_out, en]
    
    return n, interf

if __name__ == "__main__":
    n, interf = Counter()
    
    for o in n.synthesize(interf):
            print(formatVhdl(str(o)))

