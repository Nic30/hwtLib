#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import unittest

from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.utils import toRtl
from hwtLib.samples.showcase0 import Showcase0
from hwt.serializer.hwt.serializer import HwtSerializer


def readContent(file_name:str):
    THIS_DIR = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(THIS_DIR, file_name)) as f:
        return f.read()


class Showcase0TC(unittest.TestCase):
    def test_vhdl(self):
        s = toRtl(Showcase0(), serializer=VhdlSerializer)
        showcase0_vhdl = readContent("showcase0.vhd")
        self.assertEqual(s, showcase0_vhdl)

    def test_verilog(self):
        s = toRtl(Showcase0(), serializer=VerilogSerializer)
        showcase0_verilog = readContent("showcase0.v")
        self.assertEqual(s, showcase0_verilog)

    def test_systemc(self):
        s = toRtl(Showcase0(), serializer=SystemCSerializer)
        showcase0_systemc = readContent("showcase0.cpp")
        self.assertEqual(s, showcase0_systemc)

    def test_hwt(self):
        s = toRtl(Showcase0(), serializer=HwtSerializer)
        showcase0_hwt = readContent("showcase0.hwt.py")
        self.assertEqual(s, showcase0_hwt)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Showcase0TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
