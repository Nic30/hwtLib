from itertools import chain

from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axis import axis_recieve_bytes, _axis_send_bytes, packAxiSFrame
from hwtLib.peripheral.ethernet.mac import EthernetMac
from hwtLib.peripheral.ethernet.mac_tx_test import REF_FRAME, REF_CRC
from hwtLib.peripheral.ethernet.types import format_eth_addr
from pycocotb.constants import CLK_PERIOD
from hwtLib.types.ctypes import uint8_t


class EthernetMacRx_8b_TC(SingleUnitSimTestCase):
    DW = 8

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
        rx_frame_bytes = list(chain(REF_FRAME, REF_CRC))
        t = uint8_t[len(rx_frame_bytes)]
            # :attention: strb signal is reinterpreted as a keep signal
        rx_data = packAxiSFrame(self.DW, t.from_py(rx_frame_bytes),
                                withStrb=True)
        if u.USE_STRB:
            rx_data_for_agent = ((d, m, 0, last) for d, m, last in rx_data)
        else:
            rx_data_for_agent = ((d, 0, last) for d, _, last in rx_data)

        u.phy_rx._ag.data.extend(
            rx_data_for_agent
        )

        self.runSim(CLK_PERIOD * (2 * len(u.phy_rx._ag.data) + 10))
        o, f = axis_recieve_bytes(u.eth.rx)
        self.assertEqual(o, 0)
        self.assertValSequenceEqual(f, REF_FRAME)
        self.assertEmpty(u.eth.rx._ag.data)


class EthernetMacRx_32b_TC(EthernetMacRx_8b_TC):
    DW = 32


class EthernetMacRx_64b_TC(EthernetMacRx_8b_TC):
    DW = 64


EthernetMac_rx_TCs = [
    EthernetMacRx_8b_TC,
    EthernetMacRx_32b_TC,
    EthernetMacRx_64b_TC,
]


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(EthernetMacRx_8b_TC('test_single'))
    for tc in EthernetMac_rx_TCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)