#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.statements.assignmentContainer import HdlAssignmentContainer
from hwt.hdl.statements.statement import HdlStatement
from hwtLib.examples.mem.ram import SimpleAsyncRam
from hwtLib.examples.statements.ifStm import SimpleIfStatement3
from hwtLib.mem.atomic.flipReg import FlipRegister
from hwtLib.mem.cuckooHashTable import CuckooHashTable
from hwtLib.peripheral.displays.segment7 import Segment7
from hwtLib.peripheral.i2c.masterBitCntrl import I2cMasterBitCtrl
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import synthesised
from hwtLib.amba.axi_comp.oooOp.examples.counterHashTable import OooOpExampleCounterHashTable


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
        self.assertIsInstance(list(stms)[0], HdlAssignmentContainer)

    def test_index_inputs_with_assignment_has_endpoint(self):
        u = SimpleAsyncRam()
        self.check_consystency(u)

        self.assertEqual(len(u.addr_in._sigInside.endpoints), 1)
        self.assertEqual(len(u.addr_out._sigInside.endpoints), 1)

    def test_if_inputs_correc(self):
        u = Segment7()
        self.check_consystency(u)

    def test_unconnected_slices_removed_from_inputs_of_statements(self):
        u = OooOpExampleCounterHashTable()
        self.check_consystency(u)

    def test_stm_enclosure_consystency(self):
        u = I2cMasterBitCtrl()
        self.check_consystency(u)

        # test if there is not a latch
        for stm in u._ctx.statements:
            if stm._event_dependent_from_branch != 0:
                diff = stm._enclosed_for.symmetric_difference(stm._outputs)
                self.assertEqual(diff, set(), f"\n{stm}")


if __name__ == '__main__':
    unittest.main()
