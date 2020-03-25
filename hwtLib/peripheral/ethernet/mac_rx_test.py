from itertools import chain

from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axis import axis_recieve_bytes
from hwtLib.peripheral.ethernet.mac import EthernetMac
from hwtLib.peripheral.ethernet.mac_tx_test import REF_FRAME, REF_CRC
from hwtLib.peripheral.ethernet.types import format_eth_addr
from pycocotb.constants import CLK_PERIOD


class EthernetMacRx_8b_TC(SingleUnitSimTestCase):
    DW = 8
    @classmethod
    def setUpClass(cls):
        super(SingleUnitSimTestCase, cls).setUpClass()
        u = cls.getUnit()
        cls.compileSim(u, build_dir="tmp/")

    @classmethod
    def getUnit(cls):
        u = cls.u = EthernetMac()
        u.DEFAULT_MAC_ADDR = format_eth_addr(REF_FRAME[0:6])
        u.HAS_RX = True
        u.HAS_TX = False
        u.DATA_WIDTH = cls.DW
        return u

    def test_nop(self):
        u = self.u
        self.randomize(u.eth.rx)
        self.randomize(u.phy_rx)
        self.runSim(CLK_PERIOD * 10)
        self.assertEmpty(u.eth.rx._ag.data)

    def test_single(self):
        u = self.u
        u.phy_rx._ag.data.extend(
            (d, 0, last) for last, d in iter_with_last(chain(REF_FRAME, REF_CRC))
        )
        self.runSim(CLK_PERIOD * (2 * len(u.phy_rx._ag.data) + 10))
        o, f = axis_recieve_bytes(u.eth.rx)
        self.assertEqual(o, 0)
        self.assertValSequenceEqual(f, REF_FRAME)
        self.assertEmpty(u.eth.rx._ag.data)


EthernetMac_rx_TCs = [
    EthernetMacRx_8b_TC,
]


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(EthernetMacRx_8b_TC('test_single'))
    for tc in EthernetMac_rx_TCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)