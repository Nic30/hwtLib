#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.synthesizer.utils import toRtl
from hwtLib.examples.parametrization import ParametrizationExample


class ParametrizationTC(unittest.TestCase):
    def test_ParametrizationExample(self):
        toRtl(ParametrizationExample())


if __name__ == "__main__":
    # this is how you can run testcase,
    # there are many way and lots of tools support direct running of tests (like eclipse)
    suite = unittest.TestSuite()

    # this is how you can select specific test
    # suite.addTest(SimpleTC('test_simple'))

    # this is how you add all test from testcase
    suite.addTest(unittest.makeSuite(ParametrizationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
