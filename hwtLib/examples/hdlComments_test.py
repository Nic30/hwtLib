#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.synthesizer.utils import toRtl
from hwtLib.examples.hdlComments import SimpleComentedUnit, \
    simpleComentedUnit2Expected, SimpleComentedUnit3, \
    simpleComentedUnit3Expected, SimpleComentedUnit2, \
    simpleComentedUnitExpected
from hwtLib.tests.statementTrees import StatementTreesTC


class HdlCommentsTC(unittest.TestCase):
    def strStructureCmp(self, tmpl, cont):
        return StatementTreesTC.strStructureCmp(self, tmpl, cont)

    def cmp(self, compCls, expected):
        self.strStructureCmp(expected, toRtl(compCls))

    def test_SimpleComentedUnit(self):
        self.cmp(SimpleComentedUnit, simpleComentedUnitExpected)

    def test_SimpleComentedUnit2(self):
        self.cmp(SimpleComentedUnit2, simpleComentedUnit2Expected)

    def test_SimpleComentedUnit3(self):
        self.cmp(SimpleComentedUnit3, simpleComentedUnit3Expected)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(OperatorTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(HdlCommentsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
