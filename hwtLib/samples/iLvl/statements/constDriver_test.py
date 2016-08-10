import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.samples.iLvl.statements.constDriver import ConstDriverUnit


ns = HdlSimulator.ns

class ConstDriverTC(unittest.TestCase):
    def setUp(self):
        self.u = ConstDriverUnit()
        synthesised(self.u)
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=80 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/constDriver_%s.vcd" % name,
                time=time)
            
    def test_simple(self):
        u = self.u
        self.runSim("simple")
        
        self.assertSequenceEqual([0 for _ in range(8)], agInts(u.out0))
        self.assertSequenceEqual([1 for _ in range(8)], agInts(u.out1))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(ConstDriverTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
