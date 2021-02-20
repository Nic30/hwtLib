from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.fifoDrop import AxiSFifoDrop
from hwtSimApi.constants import CLK_PERIOD


class AxiSFifoDropTC(SimTestCase):
    ITEMS = 4
    DATA_WIDTH = 8

    @classmethod
    def setUpClass(cls):
        u = cls.u = AxiSFifoDrop()
        u.DATA_WIDTH = cls.DATA_WIDTH
        u.DEPTH = cls.ITEMS
        u.EXPORT_SIZE = True
        u.EXPORT_SPACE = True
        cls.compileSim(u)

    def test_nop(self):
        u = self.u
        u.dataIn_discard._ag.data.append(0)
        self.runSim(20 * CLK_PERIOD)

        self.assertEqual(len(u.dataOut._ag.data), 0)

    def test_singleWordPacket_commited(self):
        u = self.u

        u.dataIn_discard._ag.data.append(0)
        ref_data = [
            (1, 1),
        ]
        u.dataIn._ag.data.extend(ref_data)

        self.runSim(20 * CLK_PERIOD)
        self.assertValSequenceEqual(u.dataOut._ag.data, ref_data)

    def test_twoWordPacket_commited(self):
        u = self.u

        u.dataIn_discard._ag.data.append(0)
        ref_data = [
            (1, 0),
            (2, 1),
        ]
        u.dataIn._ag.data.extend(ref_data)

        self.runSim(20 * CLK_PERIOD)
        self.assertValSequenceEqual(u.dataOut._ag.data, ref_data)

    def test_commited_on_end(self):
        u = self.u

        u.dataIn_discard._ag.data.append(0)
        N = self.ITEMS - 1
        # N = 60
        ref_data = [
            (i + 1, int(last))
            for last, i in iter_with_last(range(N))
        ]
        u.dataIn._ag.data.extend(ref_data)

        self.runSim((2 * N + 10) * CLK_PERIOD)
        self.assertValSequenceEqual(u.dataOut._ag.data, ref_data)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiSFifoDropTC('test_singleWordPacket'))
    suite.addTest(unittest.makeSuite(AxiSFifoDropTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
