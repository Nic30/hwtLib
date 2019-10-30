#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import DIRECTION
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.dummyPlatform import DummyPlatform
from hwt.synthesizer.exceptions import TypeConversionErr
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.fullDuplexAxiStream import FullDuplexAxiStream
from hwtLib.examples.hierarchy.unitToUnitConnection import UnitToUnitConnection
from hwtLib.examples.simple2withNonDirectIntConnection import \
    Simple2withNonDirectIntConnection
from hwtLib.tests.synthesizer.interfaceLevel.baseSynthesizerTC import \
    BaseSynthesizerTC
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams


D = DIRECTION


def synthesised(u: Unit, targetPlatform=DummyPlatform()):
    assert not u._wasSynthetised()
    if not hasattr(u, "_interfaces"):
        u._loadDeclarations()

    for _ in u._toRtl(targetPlatform):
        pass
    return u


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


UnitWithGenericOfChild_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY ch IS
    GENERIC (NESTED_PARAM: string := "123"
    );
    PORT (a: IN STD_LOGIC_VECTOR(122 DOWNTO 0);
        b: OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ch IS
    SIGNAL tmp: STD_LOGIC_VECTOR(122 DOWNTO 0);
BEGIN
    b <= tmp;
    tmp <= a;
END ARCHITECTURE;
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY UnitWithGenericOfChild IS
    PORT (a: IN STD_LOGIC_VECTOR(122 DOWNTO 0);
        b: OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF UnitWithGenericOfChild IS
    SIGNAL sig_ch_a: STD_LOGIC_VECTOR(122 DOWNTO 0);
    SIGNAL sig_ch_b: STD_LOGIC_VECTOR(122 DOWNTO 0);
    SIGNAL tmp: STD_LOGIC_VECTOR(122 DOWNTO 0);
    COMPONENT ch IS
       GENERIC (NESTED_PARAM: string := "123"
       );
       PORT (a: IN STD_LOGIC_VECTOR(122 DOWNTO 0);
            b: OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
       );
    END COMPONENT;

BEGIN
    ch_inst: COMPONENT ch
        GENERIC MAP (NESTED_PARAM => "123"
        )
        PORT MAP (a => sig_ch_a,
            b => sig_ch_b
        );

    b <= tmp;
    sig_ch_a <= a;
    tmp <= b;
END ARCHITECTURE;"""


class SubunitsSynthesisTC(BaseSynthesizerTC):
    def test_GroupOfBlockrams(self):
        """
        Check interface directions pre and after synthesis
        """
        u = GroupOfBlockrams()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(len(u._architecture.componentInstances), 2)

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

        self.assertRaises(TypeConversionErr, lambda: toRtl(OuterUnit))

    def test_twoSubUnits(self):
        u = UnitToUnitConnection()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(len(u._architecture.componentInstances), 2)

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
        self.assertEqual(len(u._architecture.componentInstances), 3)

    def test_subUnitWithArrIntf(self):
        u = UnitWithArrIntfParent()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(len(u._architecture.componentInstances), 1)

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
        self.assertEqual(len(u._architecture.componentInstances), 4)

    def test_unitWithIntfPartsConnectedSeparately(self):
        class FDStreamConnection(Unit):
            def _declr(self):
                self.dataIn = FullDuplexAxiStream()
                self.dataOut = FullDuplexAxiStream()._m()

            def _impl(self):
                self.dataOut.tx(self.dataIn.tx)
                self.dataIn.rx(self.dataOut.rx)

        u = FDStreamConnection()
        u._loadDeclarations()
        u = synthesised(u)

    def test_used_param_from_other_unit(self):
        u = UnitWithGenericOfChild()
        s = toRtl(u, serializer=VhdlSerializer)
        self.assertEqual(s, UnitWithGenericOfChild_vhdl)


if __name__ == '__main__':
    # print(toRtl(UnitWithArrIntfParent))

    suite = unittest.TestSuite()
    # suite.addTest(SubunitsSynthesisTC('test_used_param_from_other_unit'))
    suite.addTest(unittest.makeSuite(SubunitsSynthesisTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
