import unittest

from hdl_toolkit.hdlObjects.typeShortcuts import hInt, hBool, hBit, vec
from hdl_toolkit.hdlObjects.types.defs import INT, STR
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist
from hdl_toolkit.synthesizer.rtlLevel.signalUtils.walkers import walkAllOriginSignals

andTable = [ (None, None, None),
             (None, 0, 0),
             (None, 1, None),
             (0, None, 0),
             (0, 0, 0),
             (0, 1, 0),
             (1, 1, 1)]
orTable = [ (None, None, None),
            (None, 0, None),
            (None, 1, 1),
            (0, None, None),
            (0, 0, 0),
            (0, 1, 1),
            (1, 1, 1)]


class OperatorTC(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist()
    
    def testNoBool(self):
        for v in [True, False]:
            res = ~hBool(v)
            self.assertEqual(res.val, not v)
            self.assertEqual(res.vldMask, 1)
            self.assertEqual(res.updateTime, -1)
            
    def testNotBit(self):
        for v in [False, True]:
            res = ~hBit(v)
            
            self.assertEqual(res.val, int(not v))
            self.assertEqual(res.vldMask, 1)
            self.assertEqual(res.updateTime, -1)
    
    def testBitAnd(self):
        vals = {
            1: hBit(1),
            0: hBit(0),
            None: hBit(None)
        }
        
        for a, b, expected in andTable:
            res = vals[a] & vals[b]
            expectedRes = vals[expected]
            
            self.assertEqual(expectedRes.val, res.val,
                             "%s & %s  val=%s (should be %s)" % (repr(a), repr(b), repr(res.val), repr(expectedRes.val)))
            self.assertEqual(expectedRes.vldMask, res.vldMask,
                             "%s & %s  vldMask=%s (should be %s)" % (repr(a), repr(b), repr(res.vldMask), repr(expectedRes.vldMask)))
    def testBitOr(self):
        vals = {
            1: hBit(1),
            0: hBit(0),
            None: hBit(None)
        }
        
        for a, b, expected in orTable:
            res = vals[a] | vals[b]
            expectedRes = vals[expected]
            
            self.assertEqual(expectedRes.val, res.val,
                             "%s & %s  val=%s (should be %s)" % (repr(a), repr(b), repr(res.val), repr(expectedRes.val)))
            self.assertEqual(expectedRes.vldMask, res.vldMask,
                             "%s & %s  vldMask=%s (should be %s)" % (repr(a), repr(b), repr(res.vldMask), repr(expectedRes.vldMask)))
        
    def testBoolAnd(self):
        vals = {
            1: hBool(1),
            0: hBool(0),
            None: hBool(None)
        }
        
        for a, b, expected in andTable:
            res = vals[a] & vals[b]
            expectedRes = vals[expected]
            
            self.assertEqual(expectedRes.val, res.val,
                             "%s & %s  val=%s (should be %s)" % (repr(a), repr(b), repr(res.val), repr(expectedRes.val)))
            self.assertEqual(expectedRes.vldMask, res.vldMask,
                             "%s & %s  vldMask=%s (should be %s)" % (repr(a), repr(b), repr(res.vldMask), repr(expectedRes.vldMask)))
    def testBoolOr(self):
        vals = {
            1: hBool(1),
            0: hBool(0),
            None: hBool(None)
        }
        
        for a, b, expected in orTable:
            res = vals[a] | vals[b]
            expectedRes = vals[expected]
            
            self.assertEqual(expectedRes.val, res.val,
                             "%s & %s  val=%s (should be %s)" % (repr(a), repr(b), repr(res.val), repr(expectedRes.val)))
            self.assertEqual(expectedRes.vldMask, res.vldMask,
                             "%s & %s  vldMask=%s (should be %s)" % (repr(a), repr(b), repr(res.vldMask), repr(expectedRes.vldMask)))
        
          
        
    
    def testNotNotisOrigSig(self):
        a = self.n.sig("a")
        self.assertIs(a, ~ ~a)
                    
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
            res = hInt(a_in) + hInt(b_in)
            
            b_w = 2
            
            self.assertTrue(res.vldMask)
            self.assertEqual(res.val, out, "a_in %d, b_in %d, out %d" % (a_in, b_in, out))
            
            resBit = vec(a_in, b_w) + vec(b_in, b_w)  
            self.assertEqual(resBit.vldMask, 3)
            self.assertEqual(resBit.val, out, "a_in %d, b_in %d, out %d" % (a_in, b_in, out))
    

      
if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(OperatorTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(OperatorTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
