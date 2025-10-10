#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.hdlAst._structural import HdlCompInst
from hwt.constants import DIRECTION
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.synth import to_rtl_str, synthesised
from hwt.synthesizer.exceptions import TypeConversionErr
from hwtLib.abstract.emptyHwModule import EmptyHwModule
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axi4s_fullduplex import Axi4StreamFullDuplex
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.examples.hierarchy.hwModuleToHwModuleConnection import HwModuleToHwModuleConnection
from hwtLib.examples.simpleHwModule2withNonDirectIntConnection import \
    SimpleHwModule2withNonDirectIntConnection
from hwtLib.tests.synthesizer.interfaceLevel.baseSynthesizerTC import \
    BaseSynthesizerTC


D = DIRECTION


class HwModuleWithArrHwIO(EmptyHwModule):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)
        self.USE_STRB = HwParam(True)

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            self.a = Axi4Stream()
            self.b = HwIOArray(Axi4Stream() for _ in range(2))._m()


class HwModuleWithArrHwIOParent(HwModule):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)
        self.USE_STRB = HwParam(True)

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            self.a = Axi4Stream()
            self.b0 = Axi4Stream()._m()
            self.b1 = Axi4Stream()._m()

            self.m0 = HwModuleWithArrHwIO()

    @override
    def hwImpl(self):
        self.m0.a(self.a)
        self.b0(self.m0.b[0])
        self.b1(self.m0.b[1])


class HwModuleWithGenericOnPort(HwModule):

    @override
    def hwConfig(self):
        self.NESTED_PARAM = HwParam(123)

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(self.NESTED_PARAM)
        self.b = HwIOVectSignal(self.NESTED_PARAM)._m()

    @override
    def hwImpl(self):
        tmp = self._sig("tmp", self.a._dtype)
        tmp(self.a)
        self.b(tmp)


class HwModuleWithGenericOfChild(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(123)
        self.b = HwIOVectSignal(123)._m()
        self.ch = HwModuleWithGenericOnPort()

    @override
    def hwImpl(self):
        self.ch.a(self.a)
        tmp = self._sig("tmp", self.ch.a._dtype)
        tmp(self.b)
        self.b(tmp)


def count_components(m: HwModule):
    return len([o for o in m._rtlCtx.hwModDef.objs if isinstance(o, HdlCompInst)])


class SubunitsSynthesisTC(BaseSynthesizerTC, BaseSerializationTC):
    __FILE__ = __file__

    def test_GroupOfBlockrams(self):
        """
        Check interface directions pre and after synthesis
        """
        dut = GroupOfBlockrams()
        dut._loadHwDeclarations()
        dut = synthesised(dut)
        self.assertEqual(count_components(dut), 2)

    def test_SubunitWithWrongDataT(self):

        class InternHwModule(HwModule):

            def hwDeclr(self):
                dt = HBits(64)
                self.a = HwIOSignal(dtype=dt)
                self.b = HwIOSignal(dtype=dt)._m()

            def hwImpl(self):
                self.b(self.a)

        class OuterHwModule(HwModule):

            def hwDeclr(self):
                dt = HBits(32)
                self.a = HwIOSignal(dtype=dt)
                self.b = HwIOSignal(dtype=dt)
                self.im = InternHwModule()

            def hwImpl(self):
                self.im.a(self.a)
                self.b(self.im.b)

        self.assertRaises(TypeConversionErr, lambda: to_rtl_str(OuterHwModule))

    def test_twoSubHwModules(self):
        dut = HwModuleToHwModuleConnection()
        dut._loadHwDeclarations()
        dut = synthesised(dut)
        self.assertEqual(count_components(dut), 2)

    def test_threeSubHwModules(self):

        class ThreeHwModules(HwModule):
            """a -> m0 -> m1 -> u2 -> b"""

            def hwConfig(self):
                self.DATA_WIDTH = HwParam(64)
                self.USE_STRB = HwParam(True)

            def hwDeclr(self):
                addClkRstn(self)
                with self._hwParamsShared():
                    self.a = Axi4Stream()
                    self.b = Axi4Stream()._m()

                    self.m0 = SimpleHwModule2withNonDirectIntConnection()
                    self.m1 = SimpleHwModule2withNonDirectIntConnection()
                    self.u2 = SimpleHwModule2withNonDirectIntConnection()

            def hwImpl(self):
                propagateClkRstn(self)
                self.m0.a(self.a)
                self.m1.a(self.m0.c)
                self.u2.a(self.m1.c)
                self.b(self.u2.c)

        dut = ThreeHwModules()
        dut._loadHwDeclarations()
        dut = synthesised(dut)
        self.assertEqual(count_components(dut), 3)

    def test_subHwModuleWithArrHwIO(self):
        dut = HwModuleWithArrHwIOParent()
        dut._loadHwDeclarations()
        dut = synthesised(dut)
        self.assertEqual(count_components(dut), 1)

    def test_threeLvlSubHwModulesArrHwIO(self):

        class ThreeSubunits(HwModule):
            """a -> m0 -> m1 -> u2 -> b"""

            def hwConfig(self):
                self.DATA_WIDTH = HwParam(64)
                self.USE_STRB = HwParam(True)

            def hwDeclr(self):
                addClkRstn(self)
                with self._hwParamsShared():
                    self.a = Axi4Stream()
                    self.b0 = Axi4Stream()._m()
                    self.b1 = Axi4Stream()._m()

                    self.m0 = SimpleHwModule2withNonDirectIntConnection()
                    self.m1 = HwModuleWithArrHwIO()
                    self.u2_0 = SimpleHwModule2withNonDirectIntConnection()
                    self.u2_1 = SimpleHwModule2withNonDirectIntConnection()

            def hwImpl(self):
                propagateClkRstn(self)
                self.m0.a(self.a)
                self.m1.a(self.m0.c)

                self.u2_0.a(self.m1.b[0])
                self.u2_1.a(self.m1.b[1])

                self.b0(self.u2_0.c)
                self.b1(self.u2_1.c)

        dut = ThreeSubunits()
        dut._loadHwDeclarations()
        dut = synthesised(dut)
        self.assertEqual(count_components(dut), 4)

    def test_HwModuleWithHwIOPartsConnectedSeparately(self):

        class FDStreamConnection(HwModule):

            def hwDeclr(self):
                self.dataIn = Axi4StreamFullDuplex()
                self.dataOut = Axi4StreamFullDuplex()._m()

            def hwImpl(self):
                self.dataOut.tx(self.dataIn.tx)
                self.dataIn.rx(self.dataOut.rx)

        dut = FDStreamConnection()
        dut._loadHwDeclarations()
        dut = synthesised(dut)

    def test_used_param_from_other_module(self):
        dut = HwModuleWithGenericOfChild()
        self.assert_serializes_as_file(dut, "HwModuleWithGenericOfChild.vhd")


if __name__ == '__main__':
    import unittest
    # print(to_rtl_str(HwModuleWithArrHwIOParent()))

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SubunitsSynthesisTC("test_used_param_from_other_unit")])
    suite = testLoader.loadTestsFromTestCase(SubunitsSynthesisTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
