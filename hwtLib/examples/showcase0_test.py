#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import unittest

from hwt.serializer.hwt.serializer import HwtSerializer
from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.utils import toRtl
from hwtLib.examples.showcase0 import Showcase0


class Showcase0TC(unittest.TestCase):

    def assert_same_as_file(self, s, file_name: str):
        THIS_DIR = os.path.dirname(os.path.realpath(__file__))
        fn = os.path.join(THIS_DIR, file_name)
        # with open(fn, "w") as f:
        #     f.write(s)
        with open(fn) as f:
            ref_s = f.read()
        self.assertEqual(s, ref_s)

    def test_vhdl(self):
        s = toRtl(Showcase0(), serializer=VhdlSerializer)
        self.assert_same_as_file(s, "showcase0.vhd")

    def test_verilog(self):
        s = toRtl(Showcase0(), serializer=VerilogSerializer)
        self.assert_same_as_file(s, "showcase0.v")

    def test_systemc(self):
        s = toRtl(Showcase0(), serializer=SystemCSerializer)
        self.assert_same_as_file(s, "showcase0.cpp")
    
    def test_hwt(self):
        s = toRtl(Showcase0(), serializer=HwtSerializer)
        self.assert_same_as_file(s, "showcase0.hwt.py")
    

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Showcase0TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
