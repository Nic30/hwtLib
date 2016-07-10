from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator

from hwtLib.samples.iLvl.simple import SimpleUnit

if __name__ == "__main__":
    u = SimpleUnit()

    def stimulus(s):
        aIn = True
        while True:
            # alias wait in VHDL
            yield s.wait(10 * s.ns)    
            s.write(aIn, u.a)
            aIn = not aIn
    
    simUnitVcd(u, [stimulus], "tmp/simpleUnit.vcd", time=HdlSimulator.us)
    print("done")
