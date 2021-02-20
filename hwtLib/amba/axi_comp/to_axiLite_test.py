from typing import List

from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.ram import Axi4LiteSimRam
from hwtLib.amba.axiLite_comp.to_axi_test import AxiLite_to_Axi_TC
from hwtLib.amba.axi_comp.to_axiLite import Axi_to_AxiLite
from hwtLib.amba.constants import RESP_OKAY
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


def split_frames(raw_agent_data):
    """
    :param raw_agent_data: Expected data format List[Tuple[]] where tuple is in format (frame_id, ..., last_flag)
    """
    frames = []
    frame = []
    id_ = None
    for d in raw_agent_data:
        if id_ is None:
            id_ = int(d[0])
        else:
            assert id_ == int(
                d[0]), ("All words in frame has to have same id", id_, int(d[0]))
        last = d[-1]
        frame.append(d[:-1])
        if last:
            frames.append(frame)
            frame = []
            id_ = None

    assert not frame, "unfinished frame in raw_agent_data"
    return frames


class Axi_to_AxiLite_TC(AxiLite_to_Axi_TC):
    TRANSACTION_CNT = 32
    MAX_LEN = 4

    @classmethod
    def setUpClass(cls):
        cls.u = Axi_to_AxiLite()
        cls.compileSim(cls.u)

    def create_w_frame(self, words: List[int]):
        """
        :param words: list of frame data words
        """
        strb = mask(self.u.DATA_WIDTH // 8)
        axis_data = []
        assert words, words
        for last, w in iter_with_last(words):
            axis_data.append((w, strb, int(last)))
        return axis_data

    def get_rand_in_range(self, n):
        k = n.bit_length()  # don't use (n-1) here because n can be 1
        getrandbits = self._rand.getrandbits
        r = getrandbits(k)          # 0 <= r < 2**k
        while r >= n:
            r = getrandbits(k)
        return r

    def test_read(self):
        N = 0
        u = self.u
        self.randomize_all()
        # u.m.ar._ag._debugOutput = sys.stdout
        # u.s.ar._ag._debugOutput = sys.stdout

        m = Axi4LiteSimRam(u.m)

        expected_frames = []
        for _ in range(self.TRANSACTION_CNT):
            id_ = self._rand.getrandbits(u.ID_WIDTH)
            len_ = self.get_rand_in_range(self.MAX_LEN)
            N += len_ + 1 + 1
            rand_data = [self._rand.getrandbits(u.DATA_WIDTH)
                         for _ in range(len_ + 1)]
            # rand_data = [i + 1 for i in range(len_ + 1)]
            addr = m.calloc(len_ + 1, u.DATA_WIDTH // 8, initValues=rand_data)
            # print(f"{id_:d}, 0x{addr:x}, {len_:d}", rand_data)
            a_t = u.s.ar._ag.create_addr_req(addr, len_, id_)
            u.s.ar._ag.data.append(a_t)
            expected_frames.append((addr, id_, rand_data))

        self.runSim(N * 3 * CLK_PERIOD)
        r_data = split_frames(u.s.r._ag.data)
        self.assertEqual(len(expected_frames), len(r_data), msg=[
            # expected id, len, seen id, len
            ((d0[1], len(d0[2])), (int(d1[0][0]), len(d1[0])))
            for d0, d1 in zip(expected_frames, r_data)])

        for (_, id_, expected), data in zip(expected_frames, r_data):
            expected_data = [(id_, d, RESP_OKAY) for d in expected]
            self.assertValSequenceEqual(
                data,
                expected_data
            )

    def test_write(self):
        N = self.TRANSACTION_CNT
        u = self.u

        m = Axi4LiteSimRam(u.m)

        expected_data = []
        for _ in range(self.TRANSACTION_CNT):
            id_ = self._rand.getrandbits(u.ID_WIDTH)
            len_ = self.get_rand_in_range(self.MAX_LEN)
            N += len_ + 3
            rand_data = [self._rand.getrandbits(u.DATA_WIDTH)
                         for _ in range(len_ + 1)]
            # rand_data = [i + 1 for i in range(len_ + 1)]
            addr = m.malloc((len_ + 1) * u.DATA_WIDTH // 8)
            # print(f"{id_:d}, 0x{addr:x}, {len_:d}", rand_data)
            a_t = u.s.aw._ag.create_addr_req(addr, len_, id_)
            u.s.aw._ag.data.append(a_t)

            w_frame = self.create_w_frame(rand_data)
            u.s.w._ag.data.extend(w_frame)

            word_i = addr // (u.DATA_WIDTH // 8)
            for i, d in enumerate(rand_data):
                expected_data.append((word_i + i, d))

        self.runSim(N * 3 * CLK_PERIOD)

        for word_i, expected in expected_data:
            d = m.data.get(word_i, None)
            self.assertValEqual(d, expected)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(Axi_to_AxiLite_TC('test_read'))
    suite.addTest(unittest.makeSuite(Axi_to_AxiLite_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
