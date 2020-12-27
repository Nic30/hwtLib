from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.logic.binToBcd import BinToBcd
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


def print_bcd(bcd: int, digits: int):
    digit_list = []
    for _ in range(digits):
        if bcd == 0:
            break
        d = bcd & mask(4)
        bcd >>= 4
        digit_list.append(f"{d:d}")

    if not digit_list:
        return "0"
    else:
        return "".join(reversed(digit_list))


class BinToBcdTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = BinToBcd()
        cls.u.INPUT_WIDTH = 8

        return cls.u

    def test_0to127(self):
        u = self.u

        N = 128
        u.din._ag.data.extend(range(N))
        self.runSim(CLK_PERIOD * 11 * N)

        res = u.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            self.assertEqual(print_bcd(int(d), 3), f"{i:d}")

    def test_128to255(self):
        u = self.u
        u.din._ag.data.extend(range(128, 256))
        N = 256 - 128

        self.runSim(CLK_PERIOD * 11 * N)

        res = u.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            i += 128
            self.assertEqual(print_bcd(int(d), 3), f"{i:d}")

    def test_r_96to150(self):
        u = self.u
        u.din._ag.data.extend(range(96, 150))
        N = 150 - 96
        self.randomize(u.din)
        self.randomize(u.dout)
        self.runSim(CLK_PERIOD * 20 * N)

        res = u.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            i += 96
            self.assertEqual(print_bcd(int(d), 3), f"{i:d}")


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(IndexingTC('test_split'))
    suite.addTest(unittest.makeSuite(BinToBcdTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
