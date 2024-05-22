from itertools import chain

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import axi4s_recieve_bytes, packAxi4SFrame
from hwtLib.peripheral.ethernet.mac import EthernetMac
from hwtLib.peripheral.ethernet.mac_tx_test import REF_FRAME, REF_CRC
from hwtLib.types.ctypes import uint8_t
from hwtLib.types.net.ethernet import eth_addr_format
from hwtSimApi.constants import CLK_PERIOD


class EthernetMacRx_8b_TC(SimTestCase):
    DW = 8

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = EthernetMac()
        dut.DEFAULT_MAC_ADDR = eth_addr_format(REF_FRAME[0:6])
        dut.HAS_RX = True
        dut.HAS_TX = False
        dut.DATA_WIDTH = cls.DW
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        self.randomize(dut.eth.rx)
        self.randomize(dut.phy_rx)
        self.runSim(CLK_PERIOD * 10)
        self.assertEmpty(dut.eth.rx._ag.data)

    def test_single(self):
        dut = self.dut
        rx_frame_bytes = list(chain(REF_FRAME, REF_CRC))
        t = uint8_t[len(rx_frame_bytes)]
        # :attention: strb signal is reinterpreted as a keep signal
        rx_data = packAxi4SFrame(self.DW, t.from_py(rx_frame_bytes),
                                withStrb=True)
        if dut.USE_STRB:
            rx_data_for_agent = ((d, m, 0, last) for d, m, last in rx_data)
        else:
            rx_data_for_agent = ((d, 0, last) for d, _, last in rx_data)

        dut.phy_rx._ag.data.extend(
            rx_data_for_agent
        )

        self.runSim(CLK_PERIOD * (2 * len(dut.phy_rx._ag.data) + 10))
        o, f = axi4s_recieve_bytes(dut.eth.rx)
        self.assertEqual(o, 0)
        self.assertValSequenceEqual(f, REF_FRAME)
        self.assertEmpty(dut.eth.rx._ag.data)


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
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([EthernetMacRx_8b_TC("test_single")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in EthernetMac_rx_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)