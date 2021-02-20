#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.oooOp.examples.counterArray import OooOpExampleCounterArray
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtLib.examples.errors.combLoops import freeze_set_of_sets
from hwtLib.types.ctypes import uint32_t
from hwtSimApi.constants import CLK_PERIOD


class OooOpExampleCounterArray_1w_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = OooOpExampleCounterArray()
        u.MAIN_STATE_T = uint32_t
        u.TRANSACTION_STATE_T = None
        u.ID_WIDTH = 2
        u.ADDR_WIDTH = 2 + 3
        u.DATA_WIDTH = u.MAIN_STATE_T.bit_length()
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u
        self.m = AxiSimRam(axi=u.m)
        # clear counters
        for i in range(2 ** u.ADDR_WIDTH // (u.DATA_WIDTH // 8)):
            self.m.data[i] = 0

    def test_nop(self):
        u = self.u

        self.runSim(10 * CLK_PERIOD)
        self.assertEmpty(u.dataOut._ag.data)
        self.assertEmpty(u.m.aw._ag.data)
        self.assertEmpty(u.m.w._ag.data)
        self.assertEmpty(u.m.ar._ag.data)

    def _test_incr(self, indexes=[0, ], randomize=False):
        u = self.u
        u.dataIn._ag.data.extend(indexes)

        t = (20 + len(indexes) * 2) * CLK_PERIOD
        if randomize:
            axi_randomize_per_channel(self, u.m)
            self.randomize(u.dataIn)
            self.randomize(u.dataOut)
            t *= 5

        self.runSim(t)

        # check if pipeline registers are empty
        for i in range(u.PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK):
            valid = getattr(self.rtl_simulator.model.io, f"st{i:d}_valid")
            self.assertValEqual(valid.read(), 0, i)

        # check if main state fifo is empty
        ooo_fifo = self.rtl_simulator.model.ooo_fifo_inst.io
        self.assertValEqual(ooo_fifo.item_valid.read(), 0)
        self.assertValEqual(ooo_fifo.read_wait.read(), 1)

        # check if all transactions on AXI are finished
        self.assertEmpty(u.m.b._ag.data)
        self.assertEmpty(u.m.r._ag.data)

        # check output data itself
        ref_data = [(v, indexes[:i + 1].count(v)) for i, v in enumerate(indexes)]
        self.assertValSequenceEqual(u.dataOut._ag.data, ref_data)
        for i in sorted(set(indexes)):
            self.assertValEqual(self.m.data[i], indexes.count(i), i)

    def test_incr_1x(self):
        self._test_incr([0])

    def test_incr_1xb(self):
        self._test_incr([1])

    def test_incr_2x_different(self):
        self._test_incr([0, 1])

    def test_incr_2x_same(self):
        self._test_incr([1, 1])

    def test_incr_10x_same(self):
        self._test_incr([1 for _ in range(10)])

    def test_r_incr_10x_same(self):
        d = [1 for _ in range(10)]
        self._test_incr(d, randomize=True)

    def test_r_incr_100x_random(self):
        index_pool = list(range(2 ** self.u.ID_WIDTH))
        d = [self._rand.choice(index_pool) for _ in range(100)]
        self._test_incr(d, randomize=True)

    def test_no_comb_loops(self):
        s = CombLoopAnalyzer()
        s.visit_Unit(self.u)
        comb_loops = freeze_set_of_sets(s.report())
        # for loop in comb_loops:
        #     print(10 * "-")
        #     for s in loop:
        #         print(s.resolve()[1:])

        self.assertEqual(comb_loops, frozenset())


class OooOpExampleCounterArray_0_5w_TC(OooOpExampleCounterArray_1w_TC):

    @classmethod
    def setUpClass(cls):
        u = cls.u = OooOpExampleCounterArray()
        u.MAIN_STATE_T = uint32_t
        u.TRANSACTION_STATE_T = None
        u.ID_WIDTH = 2
        u.ADDR_WIDTH = 2 + 3
        u.DATA_WIDTH = u.MAIN_STATE_T.bit_length() * 2
        cls.compileSim(u)


class OooOpExampleCounterArray_2w_TC(OooOpExampleCounterArray_1w_TC):

    @classmethod
    def setUpClass(cls):
        u = cls.u = OooOpExampleCounterArray()
        u.MAIN_STATE_T = uint32_t
        u.TRANSACTION_STATE_T = None
        u.ID_WIDTH = 2
        u.ADDR_WIDTH = 2 + 3
        u.DATA_WIDTH = u.MAIN_STATE_T.bit_length()
        u.DATA_WIDTH = u.MAIN_STATE_T.bit_length() // 2
        cls.compileSim(u)


OooOpExampleCounterArray_TCs = [
    OooOpExampleCounterArray_1w_TC,
    OooOpExampleCounterArray_0_5w_TC,
    #OooOpExampleCounterArray_2w_TC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(OooOpExampleCounterArray_1w_TC('test_r_incr_100x_random'))
    for tc in OooOpExampleCounterArray_TCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
