#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.doc_markers import internal
from hwt.hdl.operator import Operator
from hwt.hdl.operatorDefs import AllOps
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


@internal
def getBaseCond(c):
    """
    if is negated return original cond and negated flag
    """
    isNegated = False
    try:
        drivers = c.drivers
    except AttributeError:
        return (c, isNegated)

    if len(drivers) == 1:
        d = list(c.drivers)[0]
        if isinstance(d, Operator) and d.operator == AllOps.NOT:
            c = d.operands[0]
            isNegated = True

    return (c, isNegated)


class StatementTreesInternalTC(unittest.TestCase):

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
    # suite.addTest(StatementTreesInternalTC('test_basicSwitch'))
    suite.addTest(unittest.makeSuite(StatementTreesInternalTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
