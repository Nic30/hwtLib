import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.samples.iLvl.statements.switchStm import SwitchStmUnit
from hdl_toolkit.hdlObjects.specialValues import Time


class SwitchStmTC(unittest.TestCase):
    def setUp(self):
        self.u = SwitchStmUnit()
        synthesised(self.u)
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=200 * Time.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/switchStm_%s.vcd" % name,
                time=time)
            
    def test_allCases(self):
        u = self.u
        u.sel._ag.data = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 1]
        u.b._ag.data = [0, 1, 0, 0, 0, 0, 0, 0, 1, None, 0] 
        u.c._ag.data = [0, 0, 0, 1, 0, 0, 0, 0, 1, None, 0]
        u.d._ag.data = [0, 0, 0, 0, 0, 1, 0, 0, 1, None, 0]
        
        
        self.runSim("allCases")
        
        self.assertSequenceEqual([0, 1, 0, 1, 0, 1, 0, 0, 0, 0, None], agInts(u.a))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(SwitchStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
