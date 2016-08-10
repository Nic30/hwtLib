from copy import copy
import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd 
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.samples.iLvl.hierarchy.simpleSubunit import SimpleSubunit


class SimpleSubunitTC(unittest.TestCase):
   
    def testSimple(self):
        u = SimpleSubunit()
        synthesised(u)
        procs = autoAddAgents(u)
        expected = [0, 1, 0, 1, None, 0, None, 1, None, 0]
        u.a._ag.data = copy(expected)
        
        simUnitVcd(u, procs, "tmp/simpleSubunit.vcd", time=100 * HdlSimulator.ns)
        self.assertSequenceEqual(expected, agInts(u.b))
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(SimpleSubunitTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
