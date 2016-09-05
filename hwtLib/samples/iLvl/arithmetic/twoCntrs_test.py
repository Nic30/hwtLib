import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.samples.iLvl.arithmetic.twoCntrs import TwoCntrs


nineOnes = [1 for _ in range(9)]
nineZeros = [0 for _ in range(9)]
  
class TwoCntrsTC(unittest.TestCase):
    def setUp(self):
        self.u = TwoCntrs()
        synthesised(self.u)
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=90 * Time.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/twoCntrs_%s.vcd" % name,
                time=90 * Time.ns)
            
    def test_nothingEnable(self):
        u = self.u
        u.a_en._ag.data = [0]
        u.b_en._ag.data = [0]
        
        self.runSim("test_nothingEnable")
        
        self.assertSequenceEqual(nineOnes, agInts(u.eq))
        self.assertSequenceEqual(nineZeros, agInts(u.gt))
        self.assertSequenceEqual(nineZeros, agInts(u.lt))
        self.assertSequenceEqual(nineZeros, agInts(u.ne))
    
        
    def test_allEnable(self):
        u = self.u
        u.a_en._ag.data = [1]
        u.b_en._ag.data = [1]
        
        self.runSim("test_allEnable")
        self.assertSequenceEqual(nineOnes, agInts(u.eq))
        self.assertSequenceEqual(nineZeros, agInts(u.gt))
        self.assertSequenceEqual(nineZeros, agInts(u.lt))
        self.assertSequenceEqual(nineZeros, agInts(u.ne))
    

    def test_aEnable(self):
        u = self.u
        u.a_en._ag.data = [1]
        u.b_en._ag.data = [0]
        
        self.runSim("test_aEnable")
        self.assertSequenceEqual([1, 1, 0, 0, 0, 0, 0, 0, 0], agInts(u.eq))
        self.assertSequenceEqual([0, 0, 1, 1, 1, 1, 1, 1, 1], agInts(u.gt))
        self.assertSequenceEqual(nineZeros, agInts(u.lt))
        self.assertSequenceEqual([0, 0, 1, 1, 1, 1, 1, 1, 1], agInts(u.ne))
        
    def test_nonValid(self):
        u = self.u
        u.a_en._ag.data = [None]
        u.b_en._ag.data = [None]
        
        self.runSim("test_nonValid")
        self.assertSequenceEqual([1, 1, None, None, None, None, None, None, None], agInts(u.eq))
        self.assertSequenceEqual([0, 0, None, None, None, None, None, None, None], agInts(u.gt))
        self.assertSequenceEqual([0, 0, None, None, None, None, None, None, None], agInts(u.lt))
        self.assertSequenceEqual([0, 0, None, None, None, None, None, None, None], agInts(u.ne))
    
    def test_withStops(self):
        u = self.u
        u.a_en._ag.data = [0, 1, 0, 0, 1]
        u.b_en._ag.data = [0, 1, 1, 0, 0, 1]
        
        self.runSim("test_withStops")
        self.assertSequenceEqual([1, 1, 1, 0, 0, 1, 1, 1, 1], agInts(u.eq))
        self.assertSequenceEqual(nineZeros, agInts(u.gt))
        self.assertSequenceEqual([0, 0, 0, 1, 1, 0, 0, 0, 0] , agInts(u.lt))
        self.assertSequenceEqual([0, 0, 0, 1, 1, 0, 0, 0, 0] , agInts(u.ne))
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_aEnable'))
    suite.addTest(unittest.makeSuite(TwoCntrsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
