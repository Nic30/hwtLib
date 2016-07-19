import unittest
from hdl_toolkit.synthetisator.rtlLevel.netlist import RtlNetlist
from hdl_toolkit.hdlObjects.types.defs import INT, STR
from hdl_toolkit.hdlObjects.typeShortcuts import hInt, hBool, hBit, vec
from hdl_toolkit.synthetisator.rtlLevel.signalUtils.walkers import walkAllOriginSignals

class OperatorTC(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist("test")
    
    def testNoBool(self):
        for v in [True, False]:
            res =  ~hBool(v)
            self.assertEqual(res.val, not v)
            self.assertEqual(res.vldMask, 1)
            self.assertEqual(res.updateTime, -1)
            
    def testNotBit(self):
        for v in [False, True]:
            res = ~hBit(v)
            
            self.assertEqual(res.val, int(not v))
            self.assertEqual(res.vldMask, 1)
            self.assertEqual(res.updateTime, -1)
                    
    def testDownto(self):
        a = self.n.sig('a', typ=INT)
        a.defaultVal = hInt(10)
        b = hInt(0)
        r = a._downto(b)
        res = r.staticEval()
        self.assertEqual(res.val[0].val, 10)
        self.assertEqual(res.val[1].val, 0)
    
    def testwalkAllOriginSignalsDownto(self):
        a = self.n.sig('a', typ=INT)
        a.defaultVal = hInt(10)
        b = hInt(0)
        r = a._downto(b)
        origins = set(walkAllOriginSignals(r))
        self.assertSetEqual(origins, set([a]))
    
    def testwalkAllOriginSignalsDowntoAndPlus(self):
        a = self.n.sig('a', typ=INT)
        a.defaultVal = hInt(10)
        b = hInt(0)
        am = a + hInt(5)
        r = am._downto(b)
        origins = set(walkAllOriginSignals(r))
        self.assertSetEqual(origins, set([a]))
    
    def testADD_InvalidOperands(self):
        a = self.n.sig('a', typ=STR)
        b = self.n.sig('b')
        self.assertRaises(NotImplementedError, lambda : a + b) 
        
    def testAND_eval(self):
        for a_in, b_in, out in [(0, 0, 0),
                                (0, 1, 0),
                                (1, 0, 0),
                                (1, 1, 1)]:
            res = hBit(a_in) & hBit(b_in)
            self.assertEqual(res.vldMask, 1)
            self.assertEqual(res.val, out, "a_in %d, b_in %d, out %d" % (a_in, b_in, out))
    
    def testADD_eval(self):
        for a_in, b_in, out in [(0, 0, 0),
                                (0, 1, 1),
                                (1, 0, 1),
                                (1, 1, 2)]:
            res =  hInt(a_in) + hInt(b_in)
            
            b_w = 2
            
            self.assertTrue(res.vldMask)
            self.assertEqual(res.val, out, "a_in %d, b_in %d, out %d" % (a_in, b_in, out))
            
            resBit = vec(a_in, b_w) + vec(b_in, b_w)  
            self.assertEqual(resBit.vldMask, 3)
            self.assertEqual(resBit.val, out, "a_in %d, b_in %d, out %d" % (a_in, b_in, out))
    

      
if __name__ == '__main__':
    suite = unittest.TestSuite()
    #suite.addTest(OperatorTC('testADD_eval'))
    suite.addTest(unittest.makeSuite(OperatorTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
