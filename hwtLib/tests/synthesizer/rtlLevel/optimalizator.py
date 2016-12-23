#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.operatorDefs import AllOps
from hwt.hdlObjects.types.defs import BOOL
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


class Expr2CondTC(unittest.TestCase):    
    def setUp(self):
        unittest.TestCase.setUp(self)
        nl = RtlNetlist()
        self.a = nl.sig("a")
        self.b = nl.sig("b")
        self.c = nl.sig("c")
    
    def test_signalTypes(self):
        self.assertEqual(self.a.defaultVal.vldMask, 0)
    
    def test_STD_LOGIC2BoolConversion(self):
        e = self.a
        cond = e._dtype.convert(e, BOOL)
        self.assertTrue(cond.origin.operator == AllOps.EQ)
        self.assertEqual(cond.origin.ops[0], self.a, 1)
        
    def test_NotAnd(self):
        e = ~(self.a & self.b)
        self.assertEqual(e.origin.operator, AllOps.NOT)
        cond = e._convert(BOOL)
        
        self.assertEqual(cond.origin.operator, AllOps.EQ)
        _e = cond.origin.ops[0]
        self.assertEqual(e, _e)
        
        andOp = e.origin.ops[0].origin
        self.assertEqual(andOp.operator, AllOps.AND_LOG)
        
        op0 = andOp.ops[0]
        op1 = andOp.ops[1]
        
        self.assertEqual(op0, self.a)
        self.assertEqual(op1, self.b)
        

        
        
        
        
    
if __name__ == '__main__':
    unittest.main(verbosity=3)
