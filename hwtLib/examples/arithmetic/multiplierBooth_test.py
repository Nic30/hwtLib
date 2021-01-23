from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.examples.arithmetic.multiplierBooth import MultiplerBooth
from hwtSimApi.constants import CLK_PERIOD


class MultiplerBoothTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = MultiplerBooth()
        u.DATA_WIDTH = 4
        cls.u = u
        return u

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
    # suite.addTest(MultiplerBoothTC('test_possitive'))
    suite.addTest(unittest.makeSuite(MultiplerBoothTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

