#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.synthesizer.termUsageResolver import getBaseCond


class StatementTreesTC(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist("test")
    
    def test_getBaseCond(self):
        a = self.n.sig('a')
        _a = getBaseCond(~a)
        self.assertIs(a, _a[0])
        self.assertIs(True, _a[1])
        
        _a = getBaseCond(a)
        self.assertIs(a, _a[0])
        self.assertIs(False, _a[1])
        
        
        b = a < self.n.sig('b')
        _b = getBaseCond(~b)
        
        self.assertIs(b, _b[0])
        self.assertIs(True, _b[1])
        
        _b = getBaseCond(b)
        self.assertIs(b, _b[0])
        self.assertIs(False, _b[1])
        
        
if __name__ == '__main__':
    suite = unittest.TestSuite()
    #suite.addTest(StatementTreesTC('test_basicSwitch'))
    suite.addTest(unittest.makeSuite(StatementTreesTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
