#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwtLib.examples.parametrization import ParametrizationExample
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class ParametrizationTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_ParametrizationExample(self):
        self.assert_serializes_as_file(
            ParametrizationExample(), "ParametrizationExample.vhd")


if __name__ == "__main__":
    import unittest

    # this is how you can run testcase,
    # there are many way and lots of tools support direct running of tests
    # (like eclipse)
    suite = unittest.TestSuite()

    # this is how you can select specific test
    # suite.addTest(SimpleTC('test_simple'))

    # this is how you add all test from testcase
    suite.addTest(unittest.makeSuite(ParametrizationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
