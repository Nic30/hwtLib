#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.showcase0 import Showcase0


class Showcase0TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_vhdl(self):
        self.assert_serializes_as_file(Showcase0(), "showcase0.vhd")

    def test_verilog(self):
        self.assert_serializes_as_file(Showcase0(), "showcase0.v")

    def test_systemc(self):
        self.assert_serializes_as_file(Showcase0(), "showcase0.cpp")

    def test_hwt(self):
        self.assert_serializes_as_file(Showcase0(), "showcase0.hwt.py")


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(Showcase0TC("test_systemc"))
    suite.addTest(unittest.makeSuite(Showcase0TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
