import unittest

from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.ethernet.constants import ETH
from hwtLib.peripheral.ethernet.rmii_adapter import RmiiAdapter
from hwtSimApi.constants import Time


class RmiiAdapterTC(SimTestCase):
    CLK = int(Time.s / 50e6)

    @classmethod
    def setUpClass(cls):
        cls.u = RmiiAdapter()
        cls.compileSim(cls.u)

    def test_nop(self):
        u = self.u
        self.runSim(self.CLK * 100)
        self.assertEmpty(u.rx._ag.data)
        self.assertEmpty(u.eth.tx._ag.data)

    def test_rx(self):
        N = 10
        data = [i for i in range(N)]
        u = self.u
        u.eth.rx._ag._append_frame(data)
        self.runSim(self.CLK * 100)
        self.assertValSequenceEqual(
            u.rx._ag.data,
            [(d, 0, int(last)) for last, d in iter_with_last(data)])

    def test_tx(self):
        N = 10
        data = [i for i in range(N)]
        expected = [
            *[int(ETH.PREAMBLE_1B) for _ in range(7)],
            int(ETH.SFD),
            *data,
        ]
        u = self.u
        u.tx._ag.data.extend([(d, last) for last, d in iter_with_last(data)])
        self.runSim(self.CLK * 200)
        self.assertEmpty(u.eth.tx._ag.data)
        self.assertEqual(len(u.eth.tx._ag.frames), 1)
        self.assertValSequenceEqual(u.eth.tx._ag.frames[0], expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(RmiiAdapterTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(RmiiAdapterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
