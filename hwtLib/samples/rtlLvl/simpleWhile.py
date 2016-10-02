#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.serializer.vhdlFormater import formatVhdl
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist


if __name__ == "__main__":
    t = vecT(8)
    n = RtlNetlist()
    
    boundry = n.sig("boundry", t, defVal=8)
    s_out = n.sig("s_out", t)
    
    start = n.sig("start")
    en = n.sig("en")    
    
    clk = n.sig("clk")
    syncRst = n.sig("rst")
    
    
    counter = n.sig("counter", t, clk, syncRst, 0)
    If(start,
        counter ** boundry
    ).Elif(en,
        counter ** (counter - 1)
    )
    
    s_out ** counter
    
    interf = [clk, syncRst, start, en, s_out]
    
    for o in n.synthesize("simpleWhile", interf):
        print(formatVhdl(str(o)))

    
