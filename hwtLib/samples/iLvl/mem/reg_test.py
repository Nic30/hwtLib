from hwtLib.samples.iLvl.reg import DReg, DoubleDReg
from hdl_toolkit.simulator.shortcuts import simUnitVcd, afterRisingEdge, oscilate, pullDownAfter
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.synthetisator.shortcuts import toRtl
import unittest

s = HdlSimulator

class DRegTC(unittest.TestCase):
    def testSimple(self):
        u = DReg()
    
        expected = [0, 0, 1, 0, 1, 1, 0]
        recieved = []
       
        toRtl(u)
       
        def dataStimul(s):
            dIn = False
            while True:
                yield s.wait(9 * s.ns)    
                s.write(dIn, u.din)
                dIn = not dIn
        
    
        @afterRisingEdge(u.clk)
        def dataCollector(s):
            v = s.read(u.dout)
            recieved.append(v)
    
        
        simUnitVcd(u, [oscilate(u.clk, 10 * s.ns),
                       pullDownAfter(u.rst, 19 * s.ns),
                       dataStimul,
                       dataCollector,
                       ],
                   "tmp/dreg.vcd", time=75 * s.ns)
    
        # check simulation results
        self.assertEqual(len(expected), len(recieved), recieved)
        for exp, rec in zip(expected, recieved):
            self.assertTrue(rec.vldMask)
            self.assertEqual(exp, rec.val, (exp, rec))
    
    def testDouble(self):
        u = DoubleDReg()
    
        expected = [0, 0, 0, 1, 0, 1, 1]
        recieved = []
       
        toRtl(u)
       
        def dataStimul(s):
            dIn = False
            while True:
                yield s.wait(9 * s.ns)    
                s.write(dIn, u.din)
                dIn = not dIn
        
    
        @afterRisingEdge(u.clk)
        def dataCollector(s):
            v = s.read(u.dout)
            recieved.append(v)
    
        
        simUnitVcd(u, [oscilate(u.clk, 10 * s.ns),
                       pullDownAfter(u.rst, 19 * s.ns),
                       dataStimul,
                       dataCollector,
                       ],
                   "tmp/doubleDreg.vcd", time=75 * s.ns)
    
        # check simulation results
        self.assertEqual(len(expected), len(recieved), recieved)
        for exp, rec in zip(expected, recieved):
            self.assertTrue(rec.vldMask)
            self.assertEqual(exp, rec.val, (exp, rec))
        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(DRegTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)