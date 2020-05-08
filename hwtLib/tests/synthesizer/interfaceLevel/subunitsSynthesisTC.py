#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.hdlAst._structural import HdlCompInst
from hwt.hdl.constants import DIRECTION
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.exceptions import TypeConversionErr
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import to_rtl_str, synthesised
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_fullduplex import AxiStreamFullDuplex
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.examples.hierarchy.unitToUnitConnection import UnitToUnitConnection
from hwtLib.examples.simple2withNonDirectIntConnection import \
    Simple2withNonDirectIntConnection
from hwtLib.tests.synthesizer.interfaceLevel.baseSynthesizerTC import \
    BaseSynthesizerTC


D = DIRECTION


class UnitWithArrIntf(EmptyUnit):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USE_STRB = Param(True)

    def _declr(self):
        with self._paramsShared():
            self.a = AxiStream()
            self.b = HObjList(AxiStream() for _ in range(2))._m()


class UnitWithArrIntfParent(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USE_STRB = Param(True)

    def _declr(self):
        with self._paramsShared():
            self.a = AxiStream()
            self.b0 = AxiStream()._m()
            self.b1 = AxiStream()._m()

            self.u0 = UnitWithArrIntf()

    def _impl(self):
        self.u0.a(self.a)
        self.b0(self.u0.b[0])
        self.b1(self.u0.b[1])


class UnitWithGenericOnPort(Unit):
    def _config(self):
        self.NESTED_PARAM = Param(123)

    def _declr(self):
        self.a = VectSignal(self.NESTED_PARAM)
        self.b = VectSignal(self.NESTED_PARAM)._m()

    def _impl(self):
        tmp = self._sig("tmp", self.a._dtype)
        tmp(self.a)
        self.b(tmp)


class UnitWithGenericOfChild(Unit):
    def _declr(self):
        self.a = VectSignal(123)
        self.b = VectSignal(123)._m()
        self.ch = UnitWithGenericOnPort()

    def _impl(self):
        self.ch.a(self.a)
        tmp = self._sig("tmp", self.ch.a._dtype)
        tmp(self.b)
        self.b(tmp)


def count_components(u):
    return len([o for o in u._ctx.arch.objs if isinstance(o, HdlCompInst)])


class SubunitsSynthesisTC(BaseSynthesizerTC, BaseSerializationTC):
    __FILE__ = __file__

    def test_GroupOfBlockrams(self):
        """
        Check interface directions pre and after synthesis
        """
        u = GroupOfBlockrams()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(count_components(u), 2)

    def test_SubunitWithWrongDataT(self):
        class InternUnit(Unit):
            def _declr(self):
                dt = Bits(64)
                self.a = Signal(dtype=dt)
                self.b = Signal(dtype=dt)._m()

            def _impl(self):
                self.b(self.a)

        class OuterUnit(Unit):
            def _declr(self):
                dt = Bits(32)
                self.a = Signal(dtype=dt)
                self.b = Signal(dtype=dt)
                self.iu = InternUnit()

            def _impl(self):
                self.iu.a(self.a)
                self.b(self.iu.b)

        self.assertRaises(TypeConversionErr, lambda: to_rtl_str(OuterUnit))

    def test_twoSubUnits(self):
        u = UnitToUnitConnection()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(count_components(u), 2)

    def test_threeSubUnits(self):
        class ThreeSubunits(Unit):
            """a -> u0 -> u1 -> u2 -> b"""

            def _config(self):
                self.DATA_WIDTH = Param(64)
                self.USE_STRB = Param(True)

            def _declr(self):
                addClkRstn(self)
                with self._paramsShared():
                    self.a = AxiStream()
                    self.b = AxiStream()._m()

                    self.u0 = Simple2withNonDirectIntConnection()
                    self.u1 = Simple2withNonDirectIntConnection()
                    self.u2 = Simple2withNonDirectIntConnection()

            def _impl(self):
                propagateClkRstn(self)
                self.u0.a(self.a)
                self.u1.a(self.u0.c)
                self.u2.a(self.u1.c)
                self.b(self.u2.c)

        u = ThreeSubunits()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(count_components(u), 3)

    def test_subUnitWithArrIntf(self):
        u = UnitWithArrIntfParent()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(count_components(u), 1)

    def test_threeLvlSubUnitsArrIntf(self):
        class ThreeSubunits(Unit):
            """a -> u0 -> u1 -> u2 -> b"""

            def _config(self):
                self.DATA_WIDTH = Param(64)
                self.USE_STRB = Param(True)

            def _declr(self):
                addClkRstn(self)
                with self._paramsShared():
                    self.a = AxiStream()
                    self.b0 = AxiStream()._m()
                    self.b1 = AxiStream()._m()

                    self.u0 = Simple2withNonDirectIntConnection()
                    self.u1 = UnitWithArrIntf()
                    self.u2_0 = Simple2withNonDirectIntConnection()
                    self.u2_1 = Simple2withNonDirectIntConnection()

            def _impl(self):
                propagateClkRstn(self)
                self.u0.a(self.a)
                self.u1.a(self.u0.c)

                self.u2_0.a(self.u1.b[0])
                self.u2_1.a(self.u1.b[1])

                self.b0(self.u2_0.c)
                self.b1(self.u2_1.c)

        u = ThreeSubunits()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(count_components(u), 4)

    def test_unitWithIntfPartsConnectedSeparately(self):
        class FDStreamConnection(Unit):
            def _declr(self):
                self.dataIn = AxiStreamFullDuplex()
                self.dataOut = AxiStreamFullDuplex()._m()

            def _impl(self):
                self.dataOut.tx(self.dataIn.tx)
                self.dataIn.rx(self.dataOut.rx)

        u = FDStreamConnection()
        u._loadDeclarations()
        u = synthesised(u)

    def test_used_param_from_other_unit(self):
        u = UnitWithGenericOfChild()
        self.assert_serializes_as_file(u, "UnitWithGenericOfChild.vhd")


if __name__ == '__main__':
    import unittest
    # print(to_rtl_str(UnitWithArrIntfParent()))

    suite = unittest.TestSuite()
    # suite.addTest(SubunitsSynthesisTC('test_used_param_from_other_unit'))
    suite.addTest(unittest.makeSuite(SubunitsSynthesisTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
