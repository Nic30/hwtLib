#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.hdl.types.bits import Bits
from hwt.interfaces.agents.tuleWithCallback import TupleWithCallback
from hwt.interfaces.utils import propagateClkRstn
from hwt.pyUtils.arrayQuery import flatten
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.ramTransactional import RamTransactional
from hwtLib.mem.sim.segmentedArrayProxy import SegmentedArrayProxy
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask, int_list_to_int


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


class TupleWithCallback_WriteAddr(TupleWithCallback):

    def __new__(cls, id_, addr, doFlush, mem, f_addr_expected, f_data_expected, data, data_to_trans):
        t = tuple.__new__(cls, (id_, addr, doFlush))
        t.mem = mem
        t.f_addr_expected = f_addr_expected
        t.f_data_expected = f_data_expected
        t.data = data
        t.data_to_trans = data_to_trans

        return t

    def onDone(self):
        _, addr, doFlush = self
        if doFlush:
            # add current addr to flush
            # add current data to flush data
            orig_data = self.mem[addr]
            # print("flush:", addr, orig_data, "->", self.data)
            self.f_addr_expected.append((0, addr))
            self.f_data_expected.extend(self.data_to_trans(orig_data))
        # do overwrite the data in mem
        self.mem[addr] = self.data


class TupleWithCallback_ReadAddr(TupleWithCallback):

    def __new__(cls, id_, addr, mem, r_data_expected, data_to_trans):
        t = tuple.__new__(cls, (id_, addr))
        t.mem = mem
        t.r_data_expected = r_data_expected
        t.data_to_trans = data_to_trans

        return t

    def onDone(self):
        _, addr = self
        orig_data = self.mem[addr]
        # print("r:", addr, orig_data)
        self.r_data_expected.extend(self.data_to_trans(orig_data))


class RamTransactional_2wTC(SimTestCase):
    BURST_LEN = 2

    @classmethod
    def setUpClass(cls):
        cls.u = u = RamTransactionalWrap()
        u.R_ID_WIDTH = 2
        u.W_PRIV_T = Bits(2)
        u.DATA_WIDTH = 16
        u.ADDR_WIDTH = 3
        u.WORD_WIDTH = cls.BURST_LEN * u.DATA_WIDTH
        u.MAX_BLOCK_DATA_WIDTH = 8
        cls.ITEMS = 2 ** u.ADDR_WIDTH
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
        self.assertEqual(len(self.DATA), self.ITEMS)
        ae = self.assertEmpty
        ae(u.r.addr._ag.data)
        ae(u.r.data._ag.data)
        ae(u.w.addr._ag.data)
        ae(u.w.data._ag.data)
        ae(u.flush_data.addr._ag.data)
        ae(u.flush_data.data._ag.data)

    def make_item_from_index(self, i:int, MAGIC:int):
        BURST_LEN = self.BURST_LEN
        v = 0
        for w_i in range(BURST_LEN):
            v |= (i * BURST_LEN) + MAGIC + w_i << (w_i * self.u.DATA_WIDTH)
        return v

    def test_read(self, TEST_LEN=10, MAGIC=5):
        u = self.u
        BURST_LEN = self.BURST_LEN

        for i in range(min(TEST_LEN, self.ITEMS)):
            self.DATA[i] = self.make_item_from_index(i, MAGIC)

        u.r.addr._ag.data.extend(
            # (id, addr)
            [(0, i % self.ITEMS) for i in range(TEST_LEN)])

        self.runSim((TEST_LEN * BURST_LEN + 20) * CLK_PERIOD)

        r_expected = list(flatten([
            [(0,
              (i % self.ITEMS) * BURST_LEN + MAGIC + i2,
              int((i2 + 1) % BURST_LEN == 0))
              for i2 in range(BURST_LEN)
            ] for i in range(TEST_LEN)],
            level=1))

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
            [(0, i % self.ITEMS, 0) for i in range(TEST_LEN)]
        )
        u.w.data._ag.data.extend(wrData)

        self.runSim((TEST_LEN * BURST_LEN + 20) * CLK_PERIOD)

        def make_item(i):
            return self.make_item_from_index(i, MAGIC)

        self.check_memory_content(BURST_LEN, TEST_LEN, self.ITEMS, make_item, 0)
        ae = self.assertEmpty
        ae(u.r.addr._ag.data)
        ae(u.flush_data.addr._ag.data)
        ae(u.flush_data.data._ag.data)

    def check_memory_content(self, BURST_LEN, TEST_LEN, ITEMS, make_item, START_OFFSET):

        def fromat_msg(i, data_in_mem, data_expected):
            if data_in_mem._is_full_valid():
                data_in_mem = int(data_in_mem)
                return f"[{i:d}] 0x{data_in_mem:x} != 0x{data_expected:x}"
            else:
                return (i, data_in_mem)

        # check lastly written data from the beginning of the memory
        overwritten_cnt = ((START_OFFSET + TEST_LEN) // ITEMS) * TEST_LEN
        for i in range(START_OFFSET, TEST_LEN % ITEMS):
            data_expected = make_item(i * BURST_LEN + overwritten_cnt)
            data_in_mem = self.DATA[i]
            self.assertValEqual(data_in_mem, data_expected,
                msg=fromat_msg(i, data_in_mem, data_expected))

        if START_OFFSET + TEST_LEN > ITEMS and (START_OFFSET + TEST_LEN) % ITEMS != 0:
            # check the rest of the data from previous iteration
            offset = ((START_OFFSET + TEST_LEN) // ITEMS - 1) * ITEMS
            for i in range((START_OFFSET + TEST_LEN) % ITEMS, ITEMS):
                data_expected = make_item(i * BURST_LEN + offset)
                data_in_mem = self.DATA[i]
                self.assertValEqual(data_in_mem, data_expected,
                    msg=fromat_msg(i, data_in_mem, data_expected))

    def test_write_once_full(self, MAGIC=5):
        self.test_write(self.ITEMS, MAGIC)

    def test_write_twice_full(self, MAGIC=0):
        self.test_write(2 * self.ITEMS, MAGIC)

    def test_flush(self, TEST_LEN=20, MAGIC=5):
        u = self.u
        BURST_LEN = self.BURST_LEN
        MASK_ALL = mask(u.DATA_WIDTH // 8)

        wrData = u.w.data._ag.data
        wrAddr = u.w.addr._ag.data
        f_addr_expected = []
        f_data_expected = []
        # prefill the memory for later flushes
        mem = {}
        PRESET_ITEM_CNT = min(TEST_LEN, self.ITEMS)
        for i in range(PRESET_ITEM_CNT):
            item = self.make_item_from_index(i, MAGIC)
            self.DATA[i] = item
            mem[i] = item

        # dispatch write requests and build expected
        # flush transactions
        for i in range(PRESET_ITEM_CNT, TEST_LEN + PRESET_ITEM_CNT):
            item = self.make_item_from_index(i, MAGIC)
            in_mem_i = i % self.ITEMS
            orig_item = mem[in_mem_i]
            for word_i in range(BURST_LEN):
                last = int((word_i + 1) % BURST_LEN == 0)
                # (data, strb, last)
                d = (i * BURST_LEN + word_i + MAGIC, MASK_ALL, last)
                wrData.append(d)

                # (data, strb, last)
                _d = orig_item >> (u.DATA_WIDTH * word_i)
                orig_d = (int(_d) & mask(u.DATA_WIDTH), MASK_ALL, last)
                f_data_expected.append(orig_d)

            # (id, addr, flush)
            wrAddr.append((0, in_mem_i, 1))
            f_addr_expected.append((0, in_mem_i))

            mem[in_mem_i] = item

        self.runSim((TEST_LEN * BURST_LEN + 20) * CLK_PERIOD)

        def make_item2(i):
            offset = (TEST_LEN % self.ITEMS) + BURST_LEN
            return self.make_item_from_index(offset + i, MAGIC)

        self.check_memory_content(BURST_LEN, TEST_LEN, self.ITEMS, make_item2, TEST_LEN % self.ITEMS)
        self.assertValSequenceEqual(u.flush_data.addr._ag.data, f_addr_expected)
        self.assertValSequenceEqual(u.flush_data.data._ag.data, f_data_expected)

        ae = self.assertEmpty
        ae(u.r.addr._ag.data)

    def test_read_write_flush(self, TEST_LEN=50):
        u = self.u
        BURST_LEN = self.BURST_LEN
        MASK_ALL = mask(u.DATA_WIDTH // 8)

        def rand_data():
            return [self._rand.getrandbits(u.DATA_WIDTH) for _ in range(BURST_LEN)]
        # cntr = [0]
        # def rand_data():
        #     d = [cntr[0] + i for i in range(BURST_LEN)]
        #     cntr[0] += BURST_LEN
        #     return d

        def make_item(data):
            return int_list_to_int(data, u.DATA_WIDTH)

        def data_to_trans(data):
            return [
                (_d, MASK_ALL, int(last))
                for last, _d in iter_with_last(data)
            ]

        def r_data_to_trans(data):
            return [
                (0, _d, int(last))
                for last, _d in iter_with_last(data)
            ]

        # actual state of data array
        mem = {}
        # prefill data array with some values so we can check if the value was flushed sucessfully
        for i in range(self.ITEMS):
            d = rand_data()
            mem[i] = d
            self.DATA[i] = make_item(d)

        wrData = u.w.data._ag.data
        wrAddr = u.w.addr._ag.data
        rAddr = u.r.addr._ag.data
        f_addr_expected = []
        f_data_expected = []
        r_data_expected = []
        for _ in range(TEST_LEN):
            wr = self._rand.getrandbits(1)
            addr = self._rand.getrandbits(u.ADDR_WIDTH)
            if wr:
                doFlush = self._rand.getrandbits(1)
                # print("a:", addr, doFlush)
                # spot write transaction
                data = rand_data()
                wrAddr.append(TupleWithCallback_WriteAddr(
                    0, addr, doFlush, mem, f_addr_expected, f_data_expected,
                    data, data_to_trans))
                wrData.extend(data_to_trans(data))
            else:
                # stop read transaction
                rAddr.append(TupleWithCallback_ReadAddr(0, addr, mem, r_data_expected,
                                                        r_data_to_trans))

        self.runSim((TEST_LEN * BURST_LEN + 20) * CLK_PERIOD)
        ae = self.assertValSequenceEqual
        ae(u.flush_data.addr._ag.data, f_addr_expected)
        ae(u.flush_data.data._ag.data, f_data_expected)
        ae(u.r.data._ag.data, r_data_expected)


class RamTransactional_1wTC(RamTransactional_2wTC):
    BURST_LEN = 1


class RamTransactional_4wTC(RamTransactional_2wTC):
    BURST_LEN = 4


RamTransactionalTCs = [
    RamTransactional_1wTC,
    RamTransactional_2wTC,
    RamTransactional_4wTC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(RamTransactional_1wTC("test_read"))
    for tc in RamTransactionalTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
