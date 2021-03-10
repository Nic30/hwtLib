#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi_comp.cache.ramTransactional import RamTransactional
from hwtLib.mem.sim.segmentedArrayProxy import SegmentedArrayProxy
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class RamTransactionalWrap(RamTransactional):

    def _declr(self):
        RamTransactional._declr_io(self)
        with self._paramsShared():
            self.core = RamTransactional()

    def _impl(self):
        c = self.core
        c.r(self.r)
        c.w(self.w)
        self.flush_data(c.flush_data)
        propagateClkRstn(self)


class RamTransactionalTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = u = RamTransactionalWrap()
        u.ID_WIDTH = 2
        u.DATA_WIDTH = 32
        u.ADDR_WIDTH = 16
        u.WORDS_WIDTH = 64
        u.ITEMS = 32
        u.MAX_BLOCK_DATA_WIDTH = 8
        cls.BURST_LEN = u.WORDS_WIDTH // u.DATA_WIDTH
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        m = self.rtl_simulator.model
        u = self.u

        self.DATA = SegmentedArrayProxy([
                getattr(m.core_inst.data_array_inst, f"children_{i:d}_inst").io.ram_memory
                for i in range(len(u.core.data_array.children))
            ],
            words_per_item=self.BURST_LEN
        )

    def test_nop(self):
        u = self.u
        self.runSim(20 * CLK_PERIOD)
        ae = self.assertEmpty
        ae(u.r.addr._ag.data)
        ae(u.r.data._ag.data)
        ae(u.w.addr._ag.data)
        ae(u.w.data._ag.data)
        ae(u.flush_data.addr._ag.data)
        ae(u.flush_data.data._ag.data)

    def test_read(self, TEST_LEN=10, MAGIC=5):
        u = self.u
        BURST_LEN = self.BURST_LEN
        self.DATA.clean()
        for i in range(TEST_LEN):
            self.DATA[i] = ((i * 2 + 1 + MAGIC) << u.DATA_WIDTH) | (i * 2 + MAGIC)

        u.r.addr._ag.data.extend(
            # (id, addr)
            [(0, i) for i in range(TEST_LEN)])

        self.runSim((TEST_LEN + 20) * CLK_PERIOD)

        r_expected = [(0, i + MAGIC, int((i + 1) % BURST_LEN == 0))
                      for i in range(TEST_LEN * BURST_LEN)]
        self.assertValSequenceEqual(u.r.data._ag.data, r_expected)

        ae = self.assertEmpty
        ae(u.r.addr._ag.data)
        ae(u.w.addr._ag.data)
        ae(u.w.data._ag.data)
        ae(u.flush_data.addr._ag.data)
        ae(u.flush_data.data._ag.data)


    def test_read_write_flush(self, TEST_LEN=3):
        u = self.u
        BURST_LEN = self.BURST_LEN
        # def proc():
        #    yield Timer(int(CLK_PERIOD * 0.5))
        #    for i in [u.w, u.flush_data, u.r]:
        #        i._ag.setEnable(False)
        #    yield Timer(int(CLK_PERIOD * 0.3))
        #    for i in [u.w, u.flush_data, u.r]:
        #        i._ag.setEnable(True)
        #
        # self.procs.append(proc())

        # u.r.addr._ag.data.extend(
        #    # Skip write phase
        #    [NOP for _ in range(10)] +
        #    # Read during writing/flushing -> delays it after write
        #    [(0, i) for i in range(10)])
        # write_non_flushing_addr = [
        #    (0, i, 0)
        #    for i in range(TEST_LEN)
        # ]
        write_non_flushing_data = [
            (i, mask(u.DATA_WIDTH // 8), int((i + 1) % BURST_LEN == 0))
            for i in range(TEST_LEN * BURST_LEN)
        ]
        # u.w.addr._ag.data.extend(write_non_flushing_addr)
        # u.w.data._ag.data.extend(write_non_flushing_data)
        write_flushing_addr = [
            (0, i, 1)
            for i in range(TEST_LEN)
        ]
        write_flushing_data = [
            (i, mask(u.DATA_WIDTH // 8), int((i + 1) % BURST_LEN == 0))
            for i in range(TEST_LEN * BURST_LEN)
        ]
        u.w.addr._ag.data.extend(write_flushing_addr)
        u.w.data._ag.data.extend(write_flushing_data)

        self.runSim((TEST_LEN + 20) * CLK_PERIOD)

        ae = self.assertValSequenceEqual
        ae(u.r.data._ag.data, write_flushing_data, "Read data after flush mismatch")
        ae(u.flush_data.addr._ag.data, write_flushing_addr, "Flush addr mismatch")
        original_data = write_non_flushing_data
        ae(u.flush_data.data._ag.data, original_data, "Flush data mismatch")


RamTransactionalTCs = [
    RamTransactionalTC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    for tc in RamTransactionalTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
