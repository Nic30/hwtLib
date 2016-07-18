from hwtLib.mem.fifo import Fifo
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.synthetisator.shortcuts import toRtl
from hdl_toolkit.simulator.agentConnector import autoAddAgents

if __name__ == "__main__":
    
    u = Fifo()
    u.DATA_WIDTH.set(8)
    u.DEPTH.set(4)
    ns = HdlSimulator.ns
    toRtl(u)

    procs = autoAddAgents(u)
    u.din._ag.data = [1, 2, 3, 4]
    #u.dout._ag.enable = False


    simUnitVcd(u, procs,
                "tmp/fifo.vcd",
                time=80 * HdlSimulator.ns)
    print("done")
