#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.oooOp.utils import OutOfOrderCummulativeOpPipelineConfig
from hwtLib.amba.axi_comp.sim.ram import Axi4SimRam
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
        dut = cls.dut = OooOpExampleCounterArray()
        dut.MAIN_STATE_T = uint32_t
        dut.TRANSACTION_STATE_T = None
        dut.ID_WIDTH = 2
        dut.ADDR_WIDTH = 2 + 3
        dut.DATA_WIDTH = dut.MAIN_STATE_T.bit_length()
        dut.PIPELINE_CONFIG = OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=2,
                WRITE_ACK_TO_READ_DATA_LATENCY=4)
        cls.compileSim(dut)

    def setUp(self):
        SimTestCase.setUp(self)
        dut = self.dut
        self.m = Axi4SimRam(axi=dut.m)
        # clear counters
        for i in range(2 ** dut.ADDR_WIDTH // (dut.DATA_WIDTH // 8)):
            self.m.data[i] = 0

    def test_nop(self):
        dut = self.dut

        self.runSim(10 * CLK_PERIOD)
        self.assertEmpty(dut.dataOut._ag.data)
        self.assertEmpty(dut.m.aw._ag.data)
        self.assertEmpty(dut.m.w._ag.data)
        self.assertEmpty(dut.m.ar._ag.data)

    def get_counter(self, i: int):
        parts = [int(self.m.data[i * self.dut.BUS_WORD_CNT + i2]) for i2 in range(self.dut.BUS_WORD_CNT)]
        return int_list_to_int(parts, self.dut.DATA_WIDTH)

    def _test_incr(self, indexes=[0, ], randomize=False):
        # indexes = self._indexes_to_addresses(indexes)
        dut = self.dut
        dut.dataIn._ag.data.extend(indexes)

        t = (20 + len(indexes) * dut.BUS_WORD_CNT * 2) * CLK_PERIOD
        if randomize:
            axi_randomize_per_channel(self, dut.m)
            self.randomize(dut.dataIn)
            self.randomize(dut.dataOut)
            t *= 5

        states = []
        self.procs.append(OutOfOrderCummulativeOp_dump_pipeline(self, dut, self.rtl_simulator.model, states))
        try:
            self.runSim(t)
            # handle the case where something went wrong and ctl thread is still running
        finally:
            with open(f"tmp/{self.getTestName()}_pipeline.html", "w") as f:
                OutOfOrderCummulativeOp_dump_pipeline_html(f, dut, states)

        # check if pipeline registers are empty
        for i in range(dut.PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK):
            valid = getattr(self.rtl_simulator.model.io, f"st{i:d}_valid")
            self.assertValEqual(valid.read(), 0, ("stall in stage", i))

        # check if main state fifo is empty
        ooo_fifo = self.rtl_simulator.model.ooo_fifo_inst.io
        self.assertValEqual(ooo_fifo.item_valid.read(), 0, "Extra item in ooo fifo")
        self.assertValEqual(ooo_fifo.read_wait.read(), 1)

        # check if all transactions on AXI are finished
        self.assertEmpty(dut.m.b._ag.data)
        self.assertEmpty(dut.m.r._ag.data)

        # check output data itself
        ref_data = [(v, indexes[:i + 1].count(v)) for i, v in enumerate(indexes)]
        self.assertValSequenceEqual(dut.dataOut._ag.data, ref_data)
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
        index_pool = list(range(2 ** self.dut.ID_WIDTH))
        d = [self._rand.choice(index_pool) for _ in range(100)]
        self._test_incr(d, randomize=True)

    def test_r_incr_100x_random2(self):
        index_pool = [1, 2]
        d = [self._rand.choice(index_pool) for _ in range(100)]
        self._test_incr(d, randomize=True)

    def test_no_comb_loops(self):
        s = CombLoopAnalyzer()
        s.visit_HwModule(self.dut)
        comb_loops = freeze_set_of_sets(s.report())
        # for loop in comb_loops:
        #     print(10 * "-")
        #     for s in loop:
        #         print(s.resolve()[1:])

        self.assertEqual(comb_loops, frozenset())


class OooOpExampleCounterArray_0_5w_TC(OooOpExampleCounterArray_1w_TC):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = OooOpExampleCounterArray()
        dut.MAIN_STATE_T = uint32_t
        dut.TRANSACTION_STATE_T = None
        dut.ID_WIDTH = 2
        dut.ADDR_WIDTH = 2 + 3
        dut.DATA_WIDTH = dut.MAIN_STATE_T.bit_length() * 2
        dut.PIPELINE_CONFIG = OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=2,
                WRITE_ACK_TO_READ_DATA_LATENCY=4)
        cls.compileSim(dut)


class OooOpExampleCounterArray_2w_TC(OooOpExampleCounterArray_1w_TC):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = OooOpExampleCounterArray()
        dut.MAIN_STATE_T = uint32_t
        dut.TRANSACTION_STATE_T = None
        dut.ID_WIDTH = 2
        dut.ADDR_WIDTH = 2 + 3
        dut.DATA_WIDTH = dut.MAIN_STATE_T.bit_length() // 2
        dut.PIPELINE_CONFIG = OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=1,
                WRITE_ACK_TO_READ_DATA_LATENCY=4)
        cls.compileSim(dut)


class OooOpExampleCounterArray_2w_2WtoB_TC(OooOpExampleCounterArray_1w_TC):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = OooOpExampleCounterArray()
        dut.MAIN_STATE_T = uint32_t
        dut.TRANSACTION_STATE_T = None
        dut.ID_WIDTH = 2
        dut.ADDR_WIDTH = 2 + 3
        dut.DATA_WIDTH = dut.MAIN_STATE_T.bit_length() // 2
        dut.PIPELINE_CONFIG = OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=2,
                WRITE_ACK_TO_READ_DATA_LATENCY=4)
        cls.compileSim(dut)


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
