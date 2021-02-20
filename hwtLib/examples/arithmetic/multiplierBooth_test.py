from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.arithmetic.multiplierBooth import MultiplierBooth
from hwtSimApi.constants import CLK_PERIOD


class MultiplierBoothTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = u = MultiplierBooth()
        u.DATA_WIDTH = 4
        cls.compileSim(u)

    def test_possitive(self):
        u = self.u
        din = u.dataIn._ag.data
        ref = []
        for a, b in [
                (0, 0), (0, 1), (1, 0),
                (1, 1),
                (1, 2),
                (1, 2),
                (2, 2),
                (3, 2), (2, 3), (3, 3),
                (7, 3),
                (4, 5),
                (5, 4),
                (7, 7),
                ]:
            din.append((a, b))
            ref.append(a * b)

        self.runSim(CLK_PERIOD * (len(din) * u.RESULT_WIDTH + 15))

        self.assertValSequenceEqual(u.dataOut._ag.data, ref)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(MultiplierBoothTC('test_possitive'))
    suite.addTest(unittest.makeSuite(MultiplierBoothTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

