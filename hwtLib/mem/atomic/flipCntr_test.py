import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import autoAddAgents, valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.mem.atomic.flipCntr import FlipCntr


class FlipCntrTC(unittest.TestCase):
    def setUp(self):
        self.u = FlipCntr()
        synthesised(self.u)
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=90 * Time.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/flipCntr_%s.vcd" % name,
                time=90 * Time.ns)
    
    def test_nop(self):
        u = self.u
        
        u.doIncr._ag.data = [0, 0, 0, 0, 0, 0]
        self.runSim("nop")
    
        self.assertSequenceEqual([None] + [0 for _ in range(8)], valuesToInts(u.data._ag.din))
    
    def test_incr(self):
        u = self.u
        
        u.doIncr._ag.data = [0, 0, 1, 0, 0, 0]
        u.doFlip._ag.data = [0, 0, 0, 1, 0, 0]
        
        self.runSim("incr")
    
        self.assertSequenceEqual([None, 0, 0] + [1 for _ in range(6)], valuesToInts(u.data._ag.din))
    
        
    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(FlipCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
