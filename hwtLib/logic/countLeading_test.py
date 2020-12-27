from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.countLeading import CountLeadingZeros, CountLeadingOnes
from hwtSimApi.constants import CLK_PERIOD


class CountLeadingTC(SimTestCase):

    def test_CountLeadingZeros(self):
        u = CountLeadingZeros()
        u.DATA_WIDTH = 4
        self.compileSimAndStart(u)

        test_values = list(range(2 ** u.DATA_WIDTH))
        u.data_in._ag.data.extend(test_values)

        ref = []
        for v in test_values:
            leading = u.DATA_WIDTH
            while v:
                v >>= 1
                leading -= 1
            ref.append(leading)

        self.runSim((len(ref) + 1) * CLK_PERIOD)
        ref.append(0)

        self.assertValSequenceEqual(u.data_out._ag.data, ref)

    def test_CountLeadingOnes(self):
        u = CountLeadingOnes()
        u.DATA_WIDTH = 4
        self.compileSimAndStart(u)

        test_values = list(range(2 ** u.DATA_WIDTH))
        u.data_in._ag.data.extend(test_values)

        ref = []
        for v in test_values:
            x = 1 << u.DATA_WIDTH - 1
            leading = 0
            while v & x:
                x >>= 1
                leading += 1
            ref.append(leading)

        self.runSim((len(ref) + 1) * CLK_PERIOD)
        ref.append(4)

        self.assertValSequenceEqual(u.data_out._ag.data, ref)


if __name__ == '__main__':
    import sys
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CountLeadingTC))
    # suite.addTest(CountLeadingTC("test_CountLeadingZeros"))
    runner = unittest.TextTestRunner(verbosity=3)
    sys.exit(not runner.run(suite).wasSuccessful())
