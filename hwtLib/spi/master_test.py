from hwt.simulator.simTestCase import SimTestCase
from hwtLib.spi.master import SpiMaster
from hwt.hdlObjects.constants import Time


class SpiMasterTC(SimTestCase):
    def setUp(self):
        u = self.u = SpiMaster()
        u.SPI_FREQ_PESCALER.set(8)
        self.prepareUnit(u)

    def test_readAndWrite8bits(self):
        u = self.u

        # slave, d, last
        u.data._ag.data.append([0, 7, 1])
        u.spi._ag.txData.append(11)

        self.doSim(1500 * Time.ns)
        self.assertValSequenceEqual(u.data._ag.dinData, [11])
        self.assertValSequenceEqual(u.spi._ag.rxData, [7])
        self.assertValSequenceEqual(u.spi._ag.chipSelects, [0])

    def test_readAndWrite16bits(self):
        u = self.u

        # slave, d, last
        u.data._ag.data.extend(([0, 7, 0], [0, 99, 1]))
        u.spi._ag.txData.extend([11, 48])

        self.doSim(2000 * Time.ns)
        self.assertValSequenceEqual(u.data._ag.dinData, [11, 48])
        self.assertValSequenceEqual(u.spi._ag.rxData, [7, 99])
        self.assertValSequenceEqual(u.spi._ag.chipSelects, [0, 0])

    def test_readAndWrite2x8bits(self):
        u = self.u

        # slave, d, last
        u.data._ag.data.extend(([0, 7, 1], [0, 99, 1]))
        u.spi._ag.txData.extend([11, 48])

        self.doSim(2000 * Time.ns)
        self.assertValSequenceEqual(u.data._ag.dinData, [11, 48])
        self.assertValSequenceEqual(u.spi._ag.rxData, [7, 99])
        self.assertValSequenceEqual(u.spi._ag.chipSelects, [0, 0])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(ArrayBuff_writer_TC('test_fullFill_withoutAck'))
    suite.addTest(unittest.makeSuite(SpiMasterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
