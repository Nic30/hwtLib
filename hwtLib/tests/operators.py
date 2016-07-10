import unittest
from hdl_toolkit.synthetisator.rtlLevel.netlist import RtlNetlist
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.synthetisator.rtlLevel.signal.walkers import  walkAllOriginSignals
from hdl_toolkit.hdlObjects.types.defs import INT, STR, BOOL
from hdl_toolkit.hdlObjects.typeShortcuts import hInt, hBool, hBit

class OperatorTC(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist("test")
    
    def testNoOp(self):
        a = self.n.sig('a', typ=INT)

        for v in [True, False]:
            a.defaultVal = hBool(v)
            _a = a.staticEval() 
            self.assertEqual(_a.val, v)
            self.assertEqual(_a.vldMask, 1)
            self.assertEqual(_a.updateTime, -1)
            
    def testNotBOOL(self):
        a = self.n.sig('a', typ=BOOL)
        res = ~a
        for v in [False, True]:
            a.defaultVal = hBool(v)
            _res = res.staticEval()
            
            self.assertTrue(_res._eq(hBool(not v)).val)
            self.assertEqual(_res.vldMask, 1)
                    
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
        
    def testAND_LOG_eval(self):
        s0 = self.n.sig('s0')
        s1 = self.n.sig('s1')
        andOp = s0 & s1
        for a_in, b_in, out in [(0, 0, 0),
                                (0, 1, 0),
                                (1, 0, 0),
                                (1, 1, 1)]:
            s0.defaultVal = hBit(a_in)
            s1.defaultVal = hBit(b_in)
            _andOp = andOp.staticEval()
            self.assertEqual(_andOp.val, out, "a_in %d, b_in %d, out %d" % (a_in, b_in, out))
    
    def testADD_eval(self):
        a = self.n.sig('a', typ=INT)
        b = self.n.sig('b', typ=INT)
        andOp = a + b
        for a_in, b_in, out in [(0, 0, 0),
                                (0, 1, 1),
                                (1, 0, 1),
                                (1, 1, 2)]:
            a.defaultVal = hInt(a_in)
            b.defaultVal = hInt(b_in)
            v = andOp.staticEval()
            out = hInt(out)
            self.assertTrue(v._eq(out).val, "a_in %d, b_in %d, out %d" % (a_in, b_in, out.val))
             
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(OperatorTC('testDownto'))
    suite.addTest(unittest.makeSuite(OperatorTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
