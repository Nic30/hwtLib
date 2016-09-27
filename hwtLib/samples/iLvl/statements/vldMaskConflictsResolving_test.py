import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.statements.vldMaskConflictsResolving import VldMaskConflictsResolving


class VldMaskConflictsResolvingTC(unittest.TestCase):
    def setUp(self):
        u = VldMaskConflictsResolving()
        self.u, self.model, self.procs = simPrepare(u)

    def runSim(self, name, time=200 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/VldMaskConflictsResolving_%s.vcd" % name,
                time=time)
            
    def test_allCases(self):
        u = self.u
        u.a._ag.data = [0, 1, None, 0, 0, 0, 0, 0, 1, None, 0] 
        u.b._ag.data = [0, 0, 0, 1, None, 0, 0, 0, 1, None, 0]
        
        self.runSim("allCases")
        
        self.assertSequenceEqual([0, 0, 0, 1, None, 0, 0, 0, 0, 0, 0], agInts(u.c))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(VldMaskConflictsResolvingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
