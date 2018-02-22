#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.utils import toRtl
from hwtLib.samples.showcase0 import Showcase0, showcase0_vhdl, \
    showcase0_verilog, showcase0_systemc, showcase0_hwt
from hwt.serializer.hwt.serializer import HwtSerializer


class Showcase0TC(unittest.TestCase):
    def test_vhdl(self):
        s = toRtl(Showcase0(), serializer=VhdlSerializer)
        self.assertEqual(s, showcase0_vhdl)

    def test_verilog(self):
        s = toRtl(Showcase0(), serializer=VerilogSerializer)
        self.assertEqual(s, showcase0_verilog)

    def test_systemc(self):
        s = toRtl(Showcase0(), serializer=SystemCSerializer)
        self.assertEqual(s, showcase0_systemc)

    def test_hwt(self):
        s = toRtl(Showcase0(), serializer=HwtSerializer)
        self.assertEqual(s, showcase0_hwt)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Showcase0TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
