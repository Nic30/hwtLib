from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.serializer.formater import formatVhdl
from hdl_toolkit.synthesizer.codeOps import connect, If
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist


w = connect

if __name__ == "__main__":
    t = vecT(8)
    n = RtlNetlist("simpleWhile")
    
    boundry = n.sig("boundry", t, defVal=8)
    s_out = n.sig("s_out", t)
    
    start = n.sig("start")
    en = n.sig("en")    
    
    clk = n.sig("clk")
    syncRst = n.sig("rst")
    
    
    counter = n.sig("counter", t, clk, syncRst, 0)
    If(start,
        w(boundry, counter)
    ).Elif(en,
        w(counter - 1, counter)
    ).Else(
        w(counter, counter)
    )
    w(counter, s_out)
    
    interf = [clk, syncRst, start, en, s_out]
    
    for o in n.synthesize(interf):
        print(formatVhdl(str(o)))

    
