from hwtLib.samples.iLvl.cntr import Cntr

import unittest
from hdl_toolkit.synthetisator.shortcuts import toRtl
from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd


class CntrTC(unittest.TestCase):
    def setUp(self):
        self.u = Cntr()
        #print(
        toRtl(self.u)
        #)
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=90 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/cntr_%s.vcd" % name, 
                time=90 * HdlSimulator.ns)
    
    def test_overflow(self):
        u = self.u
        
        u.en._ag.data = [1]
        self.runSim("overflow")
        self.assertSequenceEqual([0, 1, 2, 3, 0, 1, 2, 3], agInts(u.val))


    def test_contingWithStops(self):
        u = self.u
        
        u.en._ag.data = [1,0,1,1,0,0,0]
        self.runSim("contingWithStops")
        self.assertSequenceEqual([0, 0, 1, 2, 2, 2, 2, 2], agInts(u.val))

    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(CntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
