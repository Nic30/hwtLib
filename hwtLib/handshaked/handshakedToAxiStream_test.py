from hwt.interfaces.std import Handshaked
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.handshakedToAxiStream import HandshakedToAxiStream
from hwtSimApi.constants import CLK_PERIOD


class HandshakedToAxiStream_MAX_FRAME_WORDS_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = HandshakedToAxiStream(Handshaked)
        u.MAX_FRAME_WORDS = 5
        cls.u = u
        cls.compileSim(u)

    def test_basic(self, N=10, randomized=True):
        u:HandshakedToAxiStream = self.u
        MAX_FRAME_WORDS = u.MAX_FRAME_WORDS
        expected = []
        for i in range(N * MAX_FRAME_WORDS):
            u.dataIn._ag.data.append(i)
            last = (i + 1) % MAX_FRAME_WORDS == 0
            expected.append((i, int(last)))

        t = (N * MAX_FRAME_WORDS + 10) * CLK_PERIOD
        if randomized:
            self.randomize(u.dataIn)
            self.randomize(u.dataOut)
            t *= 4
        self.runSim(t)
        self.assertValSequenceEqual(u.dataOut._ag.data, expected)


class HandshakedToAxiStream_IN_TIMEOUT_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = HandshakedToAxiStream(Handshaked)
        u.IN_TIMEOUT = 3
        cls.u = u
        cls.compileSim(u)

    def test_basic_no_timeout(self, N=100, randomized=False, expected_frame_lens={100}):
        self.test_basic(N=N, randomized=randomized, expected_frame_lens=expected_frame_lens)

    def test_basic(self, N=100, randomized=True, expected_frame_lens={1, 2, 3, 4, 5, 6}):
        u: HandshakedToAxiStream = self.u
        for i in range(N):
            u.dataIn._ag.data.append(i)

        t = (N + 10) * CLK_PERIOD
        if randomized:
            self.randomize(u.dataIn)
            self.randomize(u.dataOut)
            t *= 4
        self.runSim(t)
        data = []
        frame_lens = set()
        actual_len = 0
        for (d, last) in u.dataOut._ag.data:
            d = int(d)
            data.append(d)

            last = bool(last)
            actual_len += 1
            if last:
                frame_lens.add(actual_len)
                actual_len = 0
        expected_data = list(range(N))

        self.assertSequenceEqual(data, expected_data)
        self.assertSetEqual(frame_lens, expected_frame_lens)  # N dependent


class HandshakedToAxiStream_IN_TIMEOUT_AND_MAX_FRAME_WORDS_TC(HandshakedToAxiStream_IN_TIMEOUT_TC):

    @classmethod
    def setUpClass(cls):
        u = HandshakedToAxiStream(Handshaked)
        u.IN_TIMEOUT = 3
        u.MAX_FRAME_WORDS = 4
        cls.u = u
        cls.compileSim(u)

    def test_basic(self, N=100, randomized=True, expected_frame_lens={1, 2, 3, 4}):
        super(HandshakedToAxiStream_IN_TIMEOUT_AND_MAX_FRAME_WORDS_TC, self).test_basic(
            N=N, randomized=randomized, expected_frame_lens=expected_frame_lens)

    def test_basic_no_timeout(self, N=101, randomized=False, expected_frame_lens={1, 4}):
        super(HandshakedToAxiStream_IN_TIMEOUT_AND_MAX_FRAME_WORDS_TC, self).test_basic_no_timeout(
            N=N, randomized=randomized, expected_frame_lens=expected_frame_lens)


HandshakedToAxiStreamTCs = [
    HandshakedToAxiStream_MAX_FRAME_WORDS_TC,
    HandshakedToAxiStream_IN_TIMEOUT_TC,
    HandshakedToAxiStream_IN_TIMEOUT_AND_MAX_FRAME_WORDS_TC,
]


if __name__ == "__main__":
    import unittest

    suite = unittest.TestSuite()
    # suite.addTest(HandshakedToAxiStream_MAX_FRAME_WORDS_TC('test_stuckedData'))
    for tc in HandshakedToAxiStreamTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
