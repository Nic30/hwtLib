#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hdlComments import SimpleComentedHwModule, \
    SimpleComentedHwModule3, SimpleComentedHwModule2


class HdlCommentsTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_SimpleComentedHwModule(self):
        self.assert_serializes_as_file(
            SimpleComentedHwModule(), "SimpleComentedHwModule.vhd")

    def test_SimpleComentedHwModule2(self):
        self.assert_serializes_as_file(
            SimpleComentedHwModule2(), "SimpleComentedHwModule2.vhd")

    def test_SimpleComentedHwModule3(self):
        self.assert_serializes_as_file(
            SimpleComentedHwModule3(), "SimpleComentedHwModule3.vhd")


if __name__ == '__main__':
    import unittest

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HdlCommentsTC("testBitAnd")])
    suite = testLoader.loadTestsFromTestCase(HdlCommentsTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
