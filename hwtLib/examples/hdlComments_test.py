#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hdlComments import SimpleComentedUnit, \
    SimpleComentedUnit3, SimpleComentedUnit2


class HdlCommentsTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_SimpleComentedUnit(self):
        self.assert_serializes_as_file(
            SimpleComentedUnit(), "SimpleComentedUnit.vhd")

    def test_SimpleComentedUnit2(self):
        self.assert_serializes_as_file(
            SimpleComentedUnit2(), "SimpleComentedUnit2.vhd")

    def test_SimpleComentedUnit3(self):
        self.assert_serializes_as_file(
            SimpleComentedUnit3(), "SimpleComentedUnit3.vhd")


if __name__ == '__main__':
    import unittest

    suite = unittest.TestSuite()
    # suite.addTest(OperatorTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(HdlCommentsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
