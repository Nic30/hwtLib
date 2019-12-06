#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.code import If
from hwt.hdl.assignment import Assignment
from hwt.hdl.typeShortcuts import hBit
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.indexOps import IndexOps
from hwtLib.mem.atomic.flipReg import FlipRegister
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import synthesised
from hwt.hdl.statements import HdlStatement
from hwtLib.mem.cuckooHashTable import CuckooHashTable
from hwtLib.examples.statements.ifStm import SimpleIfStatement3
from hwt.synthesizer.dummyPlatform import DummyPlatform
from hwtLib.examples.mem.ram import SimpleAsyncRam
from hwtLib.peripheral.segment7 import Segment7
from hwtLib.peripheral.i2c.masterBitCntrl import I2cMasterBitCtrl


class BasicSynthesisTC(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist()

    def test_opRisingEdgeMultipletimesSameObj(self):
        clk = self.n.sig("ap_clk")
        self.assertEqual(clk._onRisingEdge(), clk._onRisingEdge())

    def test_syncSig(self):
        n = self.n
        clk = n.sig("ap_clk")
        a = n.sig("a", clk=clk)

        self.assertEqual(len(a.drivers), 1)
        _if = a.drivers[0]
        self.assertIsInstance(_if, If)

        self.assertEqual(len(_if.ifTrue), 1)
        self.assertEqual(_if.ifFalse, None)
        self.assertEqual(len(_if.elIfs), 0)

        assig = _if.ifTrue[0]
        self.assertEqual(assig.src, a.next)
        self.assertEqual(assig.dst, a)

        self.assertIs(_if.cond, clk._onRisingEdge())

    def test_syncSigWithReset(self):
        c = self.n
        clk = c.sig("ap_clk")
        rst = c.sig("ap_rst")
        a = c.sig("a", clk=clk, syncRst=rst, def_val=0)

        self.assertEqual(len(a.drivers), 1)

        _if = a.drivers[0]
        self.assertIsInstance(_if, If)

        self.assertIs(_if.cond, clk._onRisingEdge())
        self.assertEqual(len(_if.ifTrue), 1)
        self.assertEqual(_if.ifFalse, None)
        self.assertEqual(len(_if.elIfs), 0)

        if_reset = _if.ifTrue[0]

        self.assertIs(if_reset.cond, rst._isOn())
        self.assertEqual(len(if_reset.ifTrue), 1)
        self.assertEqual(len(if_reset.ifFalse), 1)
        self.assertEqual(len(if_reset.elIfs), 0)

        a_reset = if_reset.ifTrue[0]
        a_next = if_reset.ifFalse[0]
        self.assertIsInstance(a_reset, Assignment)
        self.assertEqual(a_reset.src, hBit(0))

        self.assertIsInstance(a_next, Assignment)
        self.assertEqual(a_next.src, a.next)

    def test_indexOps(self):
        c, interf = IndexOps()
        _, arch = list(c.synthesize("indexOps", interf, DummyPlatform()))

        s = VhdlSerializer.Architecture(arch, VhdlSerializer.getBaseContext())

        self.assertNotIn("sig_", s)


class StatementsConsystencyTC(unittest.TestCase):
    def check_consystency(self, u):
        synthesised(u)
        c = u._ctx
        for s in c.signals:
            for e in s.endpoints:
                if isinstance(e, HdlStatement):
                    self.assertIs(e.parentStm, None, (s, e))
                    self.assertIn(e, c.statements)
            for d in s.drivers:
                if isinstance(d, HdlStatement):
                    self.assertIs(d.parentStm, None, (s, d))
                    self.assertIn(d, c.statements)

        for stm in c.statements:
            self.assertIs(stm.parentStm, None)

    def test_if_stm_merging(self):
        u = FlipRegister()
        self.check_consystency(u)

    def test_comples_stm_ops(self):
        u = CuckooHashTable()
        self.check_consystency(u)

    def test_rm_statement(self):
        u = SimpleIfStatement3()
        self.check_consystency(u)
        stms = u._ctx.statements
        self.assertEqual(len(stms), 1)
        self.assertIsInstance(list(stms)[0], Assignment)

    def test_index_inputs_with_assignment_has_endpoint(self):
        u = SimpleAsyncRam()
        self.check_consystency(u)

        self.assertEqual(len(u.addr_in._sigInside.endpoints), 1)
        self.assertEqual(len(u.addr_out._sigInside.endpoints), 1)

    def test_if_inputs_correc(self):
        u = Segment7()
        self.check_consystency(u)

    def test_stm_enclosure_consystency(self):
        u = I2cMasterBitCtrl()
        self.check_consystency(u)

        # test there is not a latch
        for stm in u._ctx.statements:
            if not stm._is_completly_event_dependent:
                diff = stm._enclosed_for.symmetric_difference(stm._outputs)
                self.assertEqual(diff, set(), "\n%r" % stm)


if __name__ == '__main__':
    unittest.main()
