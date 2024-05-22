#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.statements.assignmentContainer import HdlAssignmentContainer
from hwt.hdl.statements.statement import HdlStatement
from hwt.hwModule import HwModule
from hwtLib.examples.axi.oooOp.counterHashTable import OooOpExampleCounterHashTable
from hwtLib.examples.mem.ram import SimpleAsyncRam
from hwtLib.examples.statements.ifStm import SimpleIfStatement3
from hwtLib.mem.atomic.flipReg import FlipRegister
from hwtLib.mem.cuckooHashTable import CuckooHashTable
from hwtLib.peripheral.displays.segment7 import Segment7
from hwtLib.peripheral.i2c.masterBitCntrl import I2cMasterBitCtrl
from hwtLib.tests.synthesizer.interfaceLevel.subHwModuleSynthesisTC import synthesised


class StatementsConsystencyTC(unittest.TestCase):
    def check_consystency(self, dut: HwModule):
        synthesised(dut)
        c = dut._ctx
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
        dut = FlipRegister()
        self.check_consystency(dut)

    def test_comples_stm_ops(self):
        dut = CuckooHashTable()
        self.check_consystency(dut)

    def test_rm_statement(self):
        dut = SimpleIfStatement3()
        self.check_consystency(dut)
        stms = dut._ctx.statements
        self.assertEqual(len(stms), 1)
        self.assertIsInstance(list(stms)[0], HdlAssignmentContainer)

    def test_index_inputs_with_assignment_has_endpoint(self):
        dut = SimpleAsyncRam()
        self.check_consystency(dut)

        self.assertEqual(len(dut.addr_in._sigInside.endpoints), 1)
        self.assertEqual(len(dut.addr_out._sigInside.endpoints), 1)

    def test_if_inputs_correc(self):
        dut = Segment7()
        self.check_consystency(dut)

    def test_unconnected_slices_removed_from_inputs_of_statements(self):
        dut = OooOpExampleCounterHashTable()
        self.check_consystency(dut)

    def test_stm_enclosure_consystency(self):
        dut = I2cMasterBitCtrl()
        self.check_consystency(dut)

        # test if there is not a latch
        for stm in dut._ctx.statements:
            if stm._event_dependent_from_branch != 0:
                diff = stm._enclosed_for.symmetric_difference(stm._outputs)
                self.assertEqual(diff, set(), f"\n{stm}")


if __name__ == '__main__':
    unittest.main()
