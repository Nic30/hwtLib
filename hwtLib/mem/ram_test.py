import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, valuesToInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthetisator.shortcuts import synthesised
from hwtLib.mem.ram import Ram_sp
from hdl_toolkit.hdlObjects.specialValues import WRITE, READ


class RamTc(unittest.TestCase):

    def test_writeAndRead(self):
        u = Ram_sp()
        u.DATA_WIDTH.set(8)
        u.ADDR_WIDTH.set(3)
        
        synthesised(u)
        procs = autoAddAgents(u)

        u.a._ag.requests = [(WRITE, 0, 5), (WRITE, 1, 7),
                            (READ, 0), (READ, 1),
                            (READ, 0), (READ, 1), (READ, 2)] 
        
        
        simUnitVcd(u, procs,
                   "tmp/ram_writeAndRead.vcd", time=80 * HdlSimulator.ns)
        self.assertSequenceEqual(valuesToInts(u._mem._val.val), [5, 7, None, None])
        self.assertSequenceEqual(valuesToInts(u.a._ag.readed), [5, 7, None, None])

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(RamTc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
