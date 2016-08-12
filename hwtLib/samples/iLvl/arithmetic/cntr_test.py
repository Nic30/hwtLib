import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.samples.iLvl.arithmetic.cntr import Cntr
from hdl_toolkit.hdlObjects.specialValues import Time


class CntrTC(unittest.TestCase):
    def setUp(self):
        self.u = Cntr()
        # print(
        synthesised(self.u)
        # )
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=90 * Time.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/cntr_%s.vcd" % name,
                time=90 * Time.ns)
    
    def test_overflow(self):
        u = self.u
        
        u.en._ag.data = [1]
        self.runSim("overflow")
        self.assertSequenceEqual([0, 0, 1, 2, 3, 0, 1, 2, 3], agInts(u.val))


    def test_contingWithStops(self):
        u = self.u
        
        u.en._ag.data = [1, 0, 1, 1, 0, 0, 0]
        self.runSim("contingWithStops")
        self.assertSequenceEqual([0, 0, 0, 1, 2, 2, 2, 2, 2], agInts(u.val))

    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(CntrTC('test_contingWithStops'))
    #suite.addTest(unittest.makeSuite(CntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
