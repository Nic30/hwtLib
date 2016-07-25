import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthetisator.shortcuts import toRtl
from hwtLib.samples.iLvl.twoCntrs import TwoCntrs


ns = HdlSimulator.ns

eightOnes = [1 for _ in range(8)]
eightZeros = [0 for _ in range(8)]
  
class TwoCntrsTC(unittest.TestCase):
    def setUp(self):
        self.u = TwoCntrs()
        # print(
        toRtl(self.u)
        # )
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=90 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/twoCntrs_%s.vcd" % name,
                time=90 * HdlSimulator.ns)
            
    def test_nothingEnable(self):
        u = self.u
        u.a_en._ag.data = [0]
        u.b_en._ag.data = [0]
        
        self.runSim("test_nothingEnable")
        
        self.assertSequenceEqual(eightOnes, agInts(u.eq))
        self.assertSequenceEqual(eightZeros, agInts(u.gt))
        self.assertSequenceEqual(eightZeros, agInts(u.lt))
        self.assertSequenceEqual(eightZeros, agInts(u.ne))
    
        
    def test_allEnable(self):
        u = self.u
        u.a_en._ag.data = [1]
        u.b_en._ag.data = [1]
        
        self.runSim("test_allEnable")
        self.assertSequenceEqual(eightOnes, agInts(u.eq))
        self.assertSequenceEqual(eightZeros, agInts(u.gt))
        self.assertSequenceEqual(eightZeros, agInts(u.lt))
        self.assertSequenceEqual(eightZeros, agInts(u.ne))
    

    def test_aEnable(self):
        u = self.u
        u.a_en._ag.data = [1]
        u.b_en._ag.data = [0]
        
        self.runSim("test_aEnable")
        self.assertSequenceEqual([1, 0, 0, 0, 0, 0, 0, 0], agInts(u.eq))
        self.assertSequenceEqual([0, 1, 1, 1, 1, 1, 1, 1], agInts(u.gt))
        self.assertSequenceEqual(eightZeros, agInts(u.lt))
        self.assertSequenceEqual([0, 1, 1, 1, 1, 1, 1, 1], agInts(u.ne))
        
    def test_nonValid(self):
        u = self.u
        u.a_en._ag.data = [None]
        u.b_en._ag.data = [None]
        
        self.runSim("test_nonValid")
        self.assertSequenceEqual([1, None, None, None, None, None, None, None], agInts(u.eq))
        self.assertSequenceEqual([0, None, None, None, None, None, None, None], agInts(u.gt))
        self.assertSequenceEqual([0, None, None, None, None, None, None, None], agInts(u.lt))
        self.assertSequenceEqual([0, None, None, None, None, None, None, None], agInts(u.ne))
    
    def test_withStops(self):
        u = self.u
        u.a_en._ag.data = [0, 1, 0, 0, 1]
        u.b_en._ag.data = [0, 1, 1, 0, 0, 1]
        
        self.runSim("test_withStops")
        self.assertSequenceEqual([1, 1, 0, 0, 1, 1, 1, 1], agInts(u.eq))
        self.assertSequenceEqual(eightZeros, agInts(u.gt))
        self.assertSequenceEqual([0, 0, 1, 1, 0, 0, 0, 0] , agInts(u.lt))
        self.assertSequenceEqual([0, 0, 1, 1, 0, 0, 0, 0] , agInts(u.ne))
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(TwoCntrsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
