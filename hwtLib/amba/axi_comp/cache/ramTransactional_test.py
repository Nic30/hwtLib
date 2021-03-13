#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi_comp.cache.ramTransactional import RamTransactional
from hwtLib.mem.sim.segmentedArrayProxy import SegmentedArrayProxy
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class RamTransactionalWrap(RamTransactional):
    """
    Wrapper for RamTransactional to make look behavior of
    the handshaked channels more readable in simulation.
    """

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
        u.DATA_WIDTH = 16
        u.ADDR_WIDTH = 10
        u.WORDS_WIDTH = 32
        u.ITEMS = 8
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

    def test_write(self, TEST_LEN=8, MAGIC=5):
        u = self.u
        BURST_LEN = self.BURST_LEN
        MASK_ALL = mask(u.DATA_WIDTH // 8)
        # (data, strb, last)
        wrData = [
            (i + MAGIC, MASK_ALL, int((i + 1) % BURST_LEN == 0))
            for i in range(TEST_LEN * BURST_LEN)
        ]
        u.w.addr._ag.data.extend(
            # (id, addr, flush)
            [(0, i, 0) for i in range(TEST_LEN)]
        )
        u.w.data._ag.data.extend(wrData)

        self.runSim((TEST_LEN * BURST_LEN + 20) * CLK_PERIOD)

        def make_item(i):
            return ((i + 1 + MAGIC) << u.DATA_WIDTH) | (i + MAGIC)

        self.check_memory_content(BURST_LEN, TEST_LEN, u.ITEMS, make_item)
        ae = self.assertEmpty
        ae(u.r.addr._ag.data)
        ae(u.flush_data.addr._ag.data)
        ae(u.flush_data.data._ag.data)

    def check_memory_content(self, BURST_LEN, TEST_LEN, ITEMS, make_item):

        def fromat_msg(i, data_in_mem, data_expected):
            if data_in_mem._is_full_valid():
                data_in_mem = int(data_in_mem)
                return f"[{i:d}] 0x{data_in_mem:x} != 0x{data_expected:x}"
            else:
                return (i, data_in_mem)

        # check lastly written data from the beginning of the memory
        overwritten_cnt = (TEST_LEN // ITEMS) * TEST_LEN
        for i in range(TEST_LEN % ITEMS):
            data_expected = make_item(i * BURST_LEN + overwritten_cnt)
            data_in_mem = self.DATA[i]
            self.assertValEqual(
                data_in_mem, data_expected,
                msg=fromat_msg(i, data_in_mem, data_expected))

        if TEST_LEN > ITEMS and TEST_LEN % ITEMS != 0:
            # check the rest of the data from previous iteration
            offset = (TEST_LEN // ITEMS - 1) * TEST_LEN
            for i in range(TEST_LEN % ITEMS, ITEMS):
                data_expected = make_item(i * BURST_LEN + offset)
                data_in_mem = self.DATA[i]
                self.assertValEqual(
                    data_in_mem, data_expected,
                    msg=fromat_msg(i, data_in_mem, data_expected))

    def test_write_once_full(self, MAGIC=5):
        self.test_write(self.u.ITEMS, MAGIC)

    def test_write_twice_full(self, MAGIC=5):
        self.test_write(2 * self.u.ITEMS, MAGIC)

    def test_flush(self, TEST_LEN=1, MAGIC=0):
        u = self.u
        BURST_LEN = self.BURST_LEN
        MASK_ALL = mask(u.DATA_WIDTH // 8)

        def make_item(i):
            return ((i + 1 + MAGIC) << u.DATA_WIDTH) | (i + MAGIC)

        wrData = u.w.data._ag.data
        wrAddr = u.w.addr._ag.data
        f_addr_expected = []
        f_data_expected = []
        # prefill the memory for later flushes
        mem = {}
        for i in range(min(TEST_LEN, u.ITEMS)):
            item = make_item(i * BURST_LEN)
            self.DATA[i] = item
            mem[i] = item

        # dispatch write requests and build expected
        # flush transactions
        for i in range(TEST_LEN, 2 * TEST_LEN):
            item = make_item(i * BURST_LEN)
            in_mem_i = (i - TEST_LEN) % u.ITEMS
            orig_item = mem[in_mem_i]
            for word_i in range(BURST_LEN):
                last = int((i - TEST_LEN + word_i + 1) % BURST_LEN == 0)
                # (data, strb, last)
                d = (i * BURST_LEN + word_i, MASK_ALL, last)
                wrData.append(d)

                # (data, strb, last)
                _d = orig_item >> (u.DATA_WIDTH * word_i)
                orig_d = (int(_d) & mask(u.DATA_WIDTH), MASK_ALL, last)
                f_data_expected.append(orig_d)

            # (id, addr, flush)
            wrAddr.append((0, in_mem_i, 1))
            f_addr_expected.append((0, in_mem_i))

            mem[in_mem_i] = item

        self.runSim((TEST_LEN + 20) * CLK_PERIOD)

        def make_item2(i):
            offset = BURST_LEN * TEST_LEN + MAGIC
            return ((i + offset + 1) << u.DATA_WIDTH) | (i + offset)

        self.check_memory_content(BURST_LEN, TEST_LEN, u.ITEMS, make_item2)
        self.assertValSequenceEqual(u.flush_data.addr._ag.data, f_addr_expected)
        self.assertValSequenceEqual(u.flush_data.data._ag.data, f_data_expected)

        ae = self.assertEmpty
        ae(u.r.addr._ag.data)

    #def test_read_write_flush(self, TEST_LEN=3):
    #    u = self.u
    #    BURST_LEN = self.BURST_LEN
    #    # def proc():
    #    #    yield Timer(int(CLK_PERIOD * 0.5))
    #    #    for i in [u.w, u.flush_data, u.r]:
    #    #        i._ag.setEnable(False)
    #    #    yield Timer(int(CLK_PERIOD * 0.3))
    #    #    for i in [u.w, u.flush_data, u.r]:
    #    #        i._ag.setEnable(True)
    #    #
    #    # self.procs.append(proc())
    #
    #    # u.r.addr._ag.data.extend(
    #    #    # Skip write phase
    #    #    [NOP for _ in range(10)] +
    #    #    # Read during writing/flushing -> delays it after write
    #    #    [(0, i) for i in range(10)])
    #    # write_non_flushing_addr = [
    #    #    (0, i, 0)
    #    #    for i in range(TEST_LEN)
    #    # ]
    #    write_non_flushing_data = [
    #        (i, mask(u.DATA_WIDTH // 8), int((i + 1) % BURST_LEN == 0))
    #        for i in range(TEST_LEN * BURST_LEN)
    #    ]
    #    # u.w.addr._ag.data.extend(write_non_flushing_addr)
    #    # u.w.data._ag.data.extend(write_non_flushing_data)
    #    write_flushing_addr = [
    #        (0, i, 1)
    #        for i in range(TEST_LEN)
    #    ]
    #    write_flushing_data = [
    #        (i, mask(u.DATA_WIDTH // 8), int((i + 1) % BURST_LEN == 0))
    #        for i in range(TEST_LEN * BURST_LEN)
    #    ]
    #    u.w.addr._ag.data.extend(write_flushing_addr)
    #    u.w.data._ag.data.extend(write_flushing_data)
    #
    #    self.runSim((TEST_LEN + 20) * CLK_PERIOD)
    #
    #    ae = self.assertValSequenceEqual
    #    ae(u.r.data._ag.data, write_flushing_data, "Read data after flush mismatch")
    #    ae(u.flush_data.addr._ag.data, write_flushing_addr, "Flush addr mismatch")
    #    original_data = write_non_flushing_data
    #    ae(u.flush_data.data._ag.data, original_data, "Flush data mismatch")


RamTransactionalTCs = [
    RamTransactionalTC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(RamTransactionalTC("test_write"))
    for tc in RamTransactionalTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
