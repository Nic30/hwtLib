#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.pyUtils.arrayQuery import balanced_reduce


class ArrayQueryTC(unittest.TestCase):

    def test_balanced_reduce(self):
        nl = RtlNetlist()
        a, b, c, d = [nl.sig(n) for n in ["a", "b", "c", "d"]]
        r = balanced_reduce([a, b, c, d], lambda a, b: a & b)
        self.assertIs(r, (a & b) & (c & d))


if __name__ == "__main__":
    import sys
    suite = unittest.TestSuite()
    # suite.addTest(ArrayQueryTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(ArrayQueryTC))
    runner = unittest.TextTestRunner(verbosity=3)
    sys.exit(not runner.run(suite).wasSuccessful())
