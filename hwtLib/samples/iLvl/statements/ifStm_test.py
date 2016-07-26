import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthetisator.shortcuts import synthesised
from hwtLib.samples.iLvl.statements.ifStm import SimpleIfStatement


ns = HdlSimulator.ns

class IfStmTC(unittest.TestCase):
    def setUp(self):
        self.u = SimpleIfStatement()
        synthesised(self.u)
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=80 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/ifStm_%s.vcd" % name,
                time=time)
            
    def test_allCases(self):
        u = self.u
        
        u.a._ag.data = [1, 1, 1,    0, 0, 0,    0, 0]
        u.b._ag.data = [0, 1, None, 0, 1, None, 1, 0] 
        u.c._ag.data = [0, 0, 0,    0, 1, 0,    0, 0]
        
        self.runSim("allCases")
        
        self.assertSequenceEqual([0, 1, None, 0, 1, None, 0, 0], agInts(u.d))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(IfStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
