from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.serializer.formater import formatVhdl
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist


if __name__ == "__main__":
    t = vecT(8)
  
    n = RtlNetlist("simpleRegister")
    
    s_out = n.sig("s_out", t)
    s_in = n.sig("s_in", t)    
    clk = n.sig("clk")
    syncRst = n.sig("rst")
    
    
    val = n.sig("val", t, clk, syncRst, 0)
    val << s_in
    s_out << val
    
    interf = [clk, syncRst, s_in, s_out]
    
    for o in n.synthesize(interf):
            print(formatVhdl(str(o)))

    
