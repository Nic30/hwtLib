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
        cls.dut = RmiiAdapter()
        cls.compileSim(cls.dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(self.CLK * 100)
        self.assertEmpty(dut.rx._ag.data)
        self.assertEmpty(dut.eth.tx._ag.data)

    def test_rx(self):
        N = 10
        data = [i for i in range(N)]
        dut = self.dut
        dut.eth.rx._ag._append_frame(data)
        self.runSim(self.CLK * 100)
        self.assertValSequenceEqual(
            dut.rx._ag.data,
            [(d, 0, int(last)) for last, d in iter_with_last(data)])

    def test_tx(self):
        N = 10
        data = [i for i in range(N)]
        expected = [
            *[int(ETH.PREAMBLE_1B) for _ in range(7)],
            int(ETH.SFD),
            *data,
        ]
        dut = self.dut
        dut.tx._ag.data.extend([(d, last) for last, d in iter_with_last(data)])
        self.runSim(self.CLK * 200)
        self.assertEmpty(dut.eth.tx._ag.data)
        self.assertEqual(len(dut.eth.tx._ag.frames), 1)
        self.assertValSequenceEqual(dut.eth.tx._ag.frames[0], expected)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([RmiiAdapterTC("test_normalOp")])
    suite = testLoader.loadTestsFromTestCase(RmiiAdapterTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
