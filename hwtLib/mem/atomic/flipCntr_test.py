import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from sp10g.stat.flipCntr import FlipCntr


class FlipCntrTC(unittest.TestCase):
    def setUp(self):
        self.u = FlipCntr()
        # print(
        synthesised(self.u)
        # )
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=90 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/flipCntr_%s.vcd" % name,
                time=90 * HdlSimulator.ns)
    
    def test_nop(self):
        u = self.u
        
        u.doIncr._ag.data = [0, 0, 0, 0, 0, 0]
        self.runSim("nop")
    
        self.assertSequenceEqual([None] + [0 for _ in range(8)], agInts(u.dataOut))
    
    def test_incr(self):
        u = self.u
        
        u.doIncr._ag.data = [0, 0, 1, 0, 0, 0]
        
        self.runSim("incr")
    
        self.assertSequenceEqual([None, 0, 0] + [1 for _ in range(6)], agInts(u.dataOut))
    
        
    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(FlipCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
