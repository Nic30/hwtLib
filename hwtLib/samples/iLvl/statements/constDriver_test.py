import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.statements.constDriver import ConstDriverUnit


class ConstDriverTC(unittest.TestCase):
    def setUp(self):
        self.u, self.model, self.procs = simPrepare(ConstDriverUnit())
        
    def runSim(self, name, time=10 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/constDriver_%s.vcd" % name,
                time=time)
            
    def test_simple(self):
        u = self.u
        self.runSim("simple")
        
        self.assertSequenceEqual([0], agInts(u.out0))
        self.assertSequenceEqual([1], agInts(u.out1))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(ConstDriverTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
