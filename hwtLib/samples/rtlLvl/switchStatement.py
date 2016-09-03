from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.serializer.formater import formatVhdl
from hdl_toolkit.synthesizer.codeOps import Switch
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist


if __name__ == "__main__":
    t = vecT(8)
    n = RtlNetlist("switchStatement")
    
    In = n.sig("input", t, defVal=8)
    Out = n.sig("output", t)
    
    Switch(In).addCases(
        [(i, Out ** (i + 1)) for i in range(8)]
    )
    
    
    interf = [In, Out]
    
    for o in n.synthesize(interf):
            print(formatVhdl(str(o)))
