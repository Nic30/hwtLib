from hwt.simulator.simTestCase import SimTestCase
from hwtLib.xilinx.slr_crossing import HsSlrCrossing
from hwtSimApi.constants import CLK_PERIOD


class HsSlrCrossingTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = HsSlrCrossing()
        dut.DATA_WIDTH = 4
        cls.compileSim(dut)

    def test_pass_data(self, randomize=True, N=50):
        dut = self.dut
        DATA = [
            self._rand.getrandbits(dut.DATA_WIDTH) for _ in range(N)
            # i for i in range(N)
        ]

        dut.s._ag.data.extend(DATA)
        t = (2 + N) * CLK_PERIOD
        if randomize:
            self.randomize(dut.s)
            self.randomize(dut.m)
            t *= 6
        self.runSim(t)

        self.assertValSequenceEqual(dut.m._ag.data, DATA)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HsSlrCrossingTC("test_passdata")])
    suite = testLoader.loadTestsFromTestCase(HsSlrCrossingTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
