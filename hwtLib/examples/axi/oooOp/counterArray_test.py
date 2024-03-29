#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.oooOp.utils import OutOfOrderCummulativeOpPipelineConfig
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtLib.examples.axi.oooOp.counterArray import OooOpExampleCounterArray
from hwtLib.examples.axi.oooOp.testUtils import OutOfOrderCummulativeOp_dump_pipeline, \
    OutOfOrderCummulativeOp_dump_pipeline_html
from hwtLib.examples.errors.combLoops import freeze_set_of_sets
from hwtLib.types.ctypes import uint32_t
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import int_list_to_int


class OooOpExampleCounterArray_1w_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = OooOpExampleCounterArray()
        u.MAIN_STATE_T = uint32_t
        u.TRANSACTION_STATE_T = None
        u.ID_WIDTH = 2
        u.ADDR_WIDTH = 2 + 3
        u.DATA_WIDTH = u.MAIN_STATE_T.bit_length()
        u.PIPELINE_CONFIG = OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=2,
                WRITE_ACK_TO_READ_DATA_LATENCY=4)
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

    def get_counter(self, i: int):
        parts = [int(self.m.data[i * self.u.BUS_WORD_CNT + i2]) for i2 in range(self.u.BUS_WORD_CNT)]
        return int_list_to_int(parts, self.u.DATA_WIDTH)

    def _test_incr(self, indexes=[0, ], randomize=False):
        # indexes = self._indexes_to_addresses(indexes)
        u = self.u
        u.dataIn._ag.data.extend(indexes)

        t = (20 + len(indexes) * u.BUS_WORD_CNT * 2) * CLK_PERIOD
        if randomize:
            axi_randomize_per_channel(self, u.m)
            self.randomize(u.dataIn)
            self.randomize(u.dataOut)
            t *= 5

        states = []
        self.procs.append(OutOfOrderCummulativeOp_dump_pipeline(self, u, self.rtl_simulator.model, states))
        try:
            self.runSim(t)
            # handle the case where something went wrong and ctl thread is still running
        finally:
            with open(f"tmp/{self.getTestName()}_pipeline.html", "w") as f:
                OutOfOrderCummulativeOp_dump_pipeline_html(f, u, states)

        # check if pipeline registers are empty
        for i in range(u.PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK):
            valid = getattr(self.rtl_simulator.model.io, f"st{i:d}_valid")
            self.assertValEqual(valid.read(), 0, ("stall in stage", i))

        # check if main state fifo is empty
        ooo_fifo = self.rtl_simulator.model.ooo_fifo_inst.io
        self.assertValEqual(ooo_fifo.item_valid.read(), 0, "Extra item in ooo fifo")
        self.assertValEqual(ooo_fifo.read_wait.read(), 1)

        # check if all transactions on AXI are finished
        self.assertEmpty(u.m.b._ag.data)
        self.assertEmpty(u.m.r._ag.data)

        # check output data itself
        ref_data = [(v, indexes[:i + 1].count(v)) for i, v in enumerate(indexes)]
        self.assertValSequenceEqual(u.dataOut._ag.data, ref_data)
        for i in sorted(set(indexes)):
            self.assertValEqual(self.get_counter(i), indexes.count(i), i)

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

    def test_r_incr_100x_random2(self):
        index_pool = [1, 2]
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
        u.PIPELINE_CONFIG = OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=2,
                WRITE_ACK_TO_READ_DATA_LATENCY=4)
        cls.compileSim(u)


class OooOpExampleCounterArray_2w_TC(OooOpExampleCounterArray_1w_TC):

    @classmethod
    def setUpClass(cls):
        u = cls.u = OooOpExampleCounterArray()
        u.MAIN_STATE_T = uint32_t
        u.TRANSACTION_STATE_T = None
        u.ID_WIDTH = 2
        u.ADDR_WIDTH = 2 + 3
        u.DATA_WIDTH = u.MAIN_STATE_T.bit_length() // 2
        u.PIPELINE_CONFIG = OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=1,
                WRITE_ACK_TO_READ_DATA_LATENCY=4)
        cls.compileSim(u)


class OooOpExampleCounterArray_2w_2WtoB_TC(OooOpExampleCounterArray_1w_TC):

    @classmethod
    def setUpClass(cls):
        u = cls.u = OooOpExampleCounterArray()
        u.MAIN_STATE_T = uint32_t
        u.TRANSACTION_STATE_T = None
        u.ID_WIDTH = 2
        u.ADDR_WIDTH = 2 + 3
        u.DATA_WIDTH = u.MAIN_STATE_T.bit_length() // 2
        u.PIPELINE_CONFIG = OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=2,
                WRITE_ACK_TO_READ_DATA_LATENCY=4)
        cls.compileSim(u)


OooOpExampleCounterArray_TCs = [
    OooOpExampleCounterArray_1w_TC,
    OooOpExampleCounterArray_0_5w_TC,
    OooOpExampleCounterArray_2w_TC,
    OooOpExampleCounterArray_2w_2WtoB_TC,
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([OooOpExampleCounterArray_2w_2WtoB_TC("test_incr_10x_same")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in OooOpExampleCounterArray_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
