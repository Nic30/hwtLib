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
    # This is one of ways how to run tests in python unittest framework (nothing HWT specific)
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(ParametrizationTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
