#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import VldSynced
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
import os
import unittest
from unittest import TestCase

from hwtLib.amba.axis import AxiStream
from hwtLib.examples.hierarchy.unitWrapper import UnitWrapper
from hwtLib.tests.statementTrees import StatementTreesTC


class ArrayIntfExample(Unit):
    """
    .. hwt-schematic::
    """

    def _declr(self):
        addClkRstn(self)
        self.a = HObjList(AxiStream() for _ in range(2))

    def _impl(self):
        for intf in self.a:
            intf.ready(1)


class UnitWithParams(Unit):
    """
    .. hwt-schematic::
    """
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.din = VldSynced()
        self.dout = VldSynced()._m()

    def _impl(self):
        self.dout(self.din)



class UnitWrapperTC(TestCase):

    def assert_same_as_file(self, s, file_name: str):
        THIS_DIR = os.path.dirname(os.path.realpath(__file__))
        fn = os.path.join(THIS_DIR, file_name)
        # with open(fn, "w") as f:
        #     f.write(s)
        with open(fn) as f:
            ref_s = f.read()
        StatementTreesTC.strStructureCmp(self, s, ref_s)


    def test_params_of_base_unit(self):
        u = UnitWithParams()
        w = UnitWrapper(u)
        s = toRtl(w, serializer=VhdlSerializer)
        self.assert_same_as_file(s, "UnitWithParams_in_wrap.vhd")

    def test_interfaces(self):
        u = UnitWrapper(ArrayIntfExample())
        toRtl(u)
        self.assertTrue(hasattr(u, "a_0"))
        self.assertTrue(hasattr(u, "a_1"))
        self.assertFalse(hasattr(u, "a"))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UnitWrapperTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
