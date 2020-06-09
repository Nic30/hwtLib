from hwt.simulator.simTestCase import SingleUnitSimTestCase, allValuesToInts
from pyMathBitPrecise.bit_utils import mask, set_bit_range
from pycocotb.constants import CLK_PERIOD

from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.cache.store_buffer import AxiStoreBuffer
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwt.pyUtils.arrayQuery import iter_with_last


class AxiStoreBuffer_1word_per_cachelineTC(SingleUnitSimTestCase):
    # DEFAULT_BUILD_DIR = "."
    # RECOMPILE = False

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiStoreBuffer()
        u.ADDR_WIDTH = 16
        u.ID_WIDTH = 2
        u.CACHE_LINE_SIZE = 4
        u.DATA_WIDTH = 32
        u.MAX_BLOCK_DATA_WIDTH = 8
        return u

    def randomize_all(self):
        self.randomize(self.u.w)
        axi_randomize_per_channel(self, self.u.bus)
        # self.randomize(self.u.bus.aw)
        # self.randomize(self.u.bus.w)
        # self.randomize(self.u.bus.b)

    def test_nop(self, randomized=False):
        if randomized:
            self.randomize_all()

        self.runSim(10 * CLK_PERIOD)
        u = self.u
        self.assertEmpty(u.bus.aw._ag.data)
        self.assertEmpty(u.bus.w._ag.data)

    def test_nop_randomized(self):
        self.test_nop(randomized=True)

    def test_non_mergable_no_ack(self, N=10, randomized=False):
        u = self.u
        u.w._ag.data.extend((i, 10 + i, mask(u.CACHE_LINE_SIZE)) for i in range(N))
        if randomized:
            self.randomize_all()

        self.runSim((N + 10) * 2 * CLK_PERIOD * u.BUS_WORDS_IN_CACHELINE)

        SIZE = 2 ** u.ID_WIDTH
        aw = u.bus.aw._ag
        self.assertValSequenceEqual(aw.data, [
            aw.create_addr_req(addr=u.CACHE_LINE_SIZE * i,
                               _len=u.BUS_WORDS_IN_CACHELINE - 1,
                               _id=i)
            for i in range(N)
        ])

        w_ref = []
        for i in range(min(SIZE, N)):
            for last, w_i in iter_with_last(range(u.BUS_WORDS_IN_CACHELINE)):
                d = (10 + i if w_i == 0 else 0, mask(u.DATA_WIDTH // 8), int(last))
                w_ref.append(d)
        for i, (x0, x1) in enumerate(zip(u.bus.w._ag.data, w_ref)):
            print(i, allValuesToInts(x0), x1)

        self.assertValSequenceEqual(u.bus.w._ag.data, w_ref)

        # 1 item is currently handled by agent, 1 item in tmp reg
        self.assertEqual(len(u.w._ag.data), N - SIZE - 1 - 1)

    def test_non_mergable_no_ack_randomized(self, N=10):
        self.test_non_mergable_no_ack(N, randomized=True)

    def test_single_write(self):
        u = self.u
        u.w._ag.data.append((1, 11, mask(u.CACHE_LINE_SIZE)))
        self.runSim(10 * CLK_PERIOD)

        aw = u.bus.aw._ag
        self.assertValSequenceEqual(aw.data, [
            aw.create_addr_req(addr=1 * u.CACHE_LINE_SIZE,
                               _len=u.BUS_WORDS_IN_CACHELINE - 1,
                               _id=0),
        ])
        self.assertValSequenceEqual(u.bus.w._ag.data, [
            (11 if i == 0 else 0, mask(u.DATA_WIDTH // 8), int(last))
            for last, i in iter_with_last(range(u.BUS_WORDS_IN_CACHELINE))
        ])

    def test_with_mem(self, N=10, randomized=False):
        u = self.u
        mem = AxiSimRam(u.bus)
        u.w._ag.data.extend((i, 10 + i, mask(4)) for i in range(N))
        if randomized:
            self.randomize_all()

        self.runSim((N + 10) * 3 * CLK_PERIOD)
        mem_val = mem.getArray(0, u.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(mem_val, [10 + i for i in range(N)])

    def test_with_mem_randomized(self, N=10):
        self.test_with_mem(N=N, randomized=True)

    def test_mergable(self, N=10, ADDRESSES=[0, ], randomized=False):
        u = self.u
        mem = AxiSimRam(u.bus)
        expected = {}
        for a in ADDRESSES:
            for i in range(N):
                B_i = (i % 4)
                d = i << (B_i * 8)
                m = 1 << B_i
                u.w._ag.data.append((a, d, m))
                v = expected.get(a, 0)
                v = set_bit_range(v, B_i * 8, 8, i)
                expected[a] = v

        if randomized:
            self.randomize_all()

        self.runSim((N * len(ADDRESSES) + 10) * 3 * CLK_PERIOD)
        for a in ADDRESSES:
            self.assertValEqual(mem.data[a], expected[a], "%d: 0x%08x" % (a, expected[a]))

    def test_mergable2(self, N=10, ADDRESSES=[0, ], randomized=False):
        """
        same as test_mergable just the inner cycle is reversed
        """
        u = self.u
        mem = AxiSimRam(u.bus)
        expected = {}
        for i in range(N):
            for a in ADDRESSES:
                B_i = (i % 4)
                d = i << (B_i * 8)
                m = 1 << B_i
                u.w._ag.data.append((a, d, m))
                v = expected.get(a, 0)
                v = set_bit_range(v, B_i * 8, 8, i)
                expected[a] = v

        if randomized:
            self.randomize_all()

        self.runSim((N * len(ADDRESSES) + 10) * 3 * CLK_PERIOD)
        for a in ADDRESSES:
            self.assertValEqual(mem.data[a], expected[a], "%d: 0x%08x" % (a, expected[a]))

    def test_mergable_4_address(self, N=10, ADDRESSES=[1, 2, 3, 4], randomized=False):
        self.test_mergable(N, ADDRESSES, randomized)

    def test_mergable_randomized(self, N=10, ADDRESSES=[0, ]):
        self.test_mergable(N, ADDRESSES, randomized=True)

    def test_mergable_4_address_randomized(self, N=10, ADDRESSES=[1, 2, 3, 4]):
        self.test_mergable(N, ADDRESSES, randomized=True) 


class AxiStoreBuffer_2words_per_cachelineTC(AxiStoreBuffer_1word_per_cachelineTC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiStoreBuffer()
        u.ADDR_WIDTH = 16
        u.ID_WIDTH = 2
        u.CACHE_LINE_SIZE = 8
        u.DATA_WIDTH = 32
        u.MAX_BLOCK_DATA_WIDTH = 8
        return u


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    suite.addTest(AxiStoreBuffer_2words_per_cachelineTC('test_non_mergable_no_ack_randomized'))
    # suite.addTest(unittest.makeSuite(AxiStoreBuffer_1word_per_cachelineTC))
    # suite.addTest(unittest.makeSuite(AxiStoreBuffer_2words_per_cachelineTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
