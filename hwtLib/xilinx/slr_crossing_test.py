from hwtLib.xilinx.slr_crossing import HsSlrCrossing
from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD


class HsSlrCrossingTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = HsSlrCrossing()
        u.DATA_WIDTH = 4
        cls.compileSim(u)

    def test_pass_data(self, randomize=True, N=50):
        u = self.u
        DATA = [
            self._rand.getrandbits(u.DATA_WIDTH) for _ in range(N)
            # i for i in range(N)
        ]

        u.s._ag.data.extend(DATA)
        t = (2 + N) * CLK_PERIOD
        if randomize:
            self.randomize(u.s)
            self.randomize(u.m)
            t *= 6
        self.runSim(t)

        self.assertValSequenceEqual(u.m._ag.data, DATA)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HsFifoTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsSlrCrossingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
