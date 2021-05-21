from binascii import crc32

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import axis_send_bytes, axis_recieve_bytes
from hwtLib.peripheral.ethernet.mac import EthernetMac
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import byte_list_to_be_int


REF_FRAME = [
    0x00, 0x0A, 0xE6, 0xF0, 0x05, 0xA3, 0x00, 0x12,
    0x34, 0x56, 0x78, 0x90, 0x08, 0x00, 0x45, 0x00,
    0x00, 0x30, 0xB3, 0xFE, 0x00, 0x00, 0x80, 0x11,
    0x72, 0xBA, 0x0A, 0x00, 0x00, 0x03, 0x0A, 0x00,
    0x00, 0x02, 0x04, 0x00, 0x04, 0x00, 0x00, 0x1C,
    0x89, 0x4D, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
    0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D,
    0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13]
REF_CRC = [0x7A, 0xD5, 0x6B, 0xB3]


class EthernetMacTx_8b_TC(SimTestCase):
    DW = 8
    # [TODO]: tests for packet drop on every error
    @classmethod
    def setUpClass(cls):
        u = cls.u = EthernetMac()
        u.HAS_RX = False
        u.DATA_WIDTH = cls.DW
        cls.compileSim(u)

    def test_nop(self):
        u = self.u
        self.runSim(CLK_PERIOD * 10)
        self.assertEmpty(u.phy_tx._ag.data)

    def pop_tx_frame(self):
        return axis_recieve_bytes(self.u.phy_tx)

    def send_tx_frame(self, data):
        axis_send_bytes(self.u.eth.tx, data)

    def test_single(self):
        ref_data = REF_FRAME
        crc_ref = REF_CRC
        crc_ref = byte_list_to_be_int(crc_ref)
        u = self.u
        axis_send_bytes(u.eth.tx, ref_data)
        self.runSim(CLK_PERIOD * (len(ref_data) * 2 + 10))
        f = self.pop_tx_frame()
        self.assertEqual(f[0], 0)  # frame offset
        f = f[1]

        self.assertEqual(len(f), len(ref_data) + 4)
        data = f[:-4]
        self.assertValSequenceEqual(data, ref_data)

        crc = f[-4:]
        crc = byte_list_to_be_int(crc)
        py_crc = crc32(bytes(data))
        self.assertEqual(
            crc, crc32(bytes(data)),
            "0x{0:8x} 0x{1:8x}".format(crc_ref, py_crc))
        self.assertEqual(
            crc, crc32(bytes(data)),
            "0x{0:8x} 0x{1:8x}".format(crc, crc_ref))
        self.assertEmpty(u.phy_tx._ag.data)

    def test_frames_random_space(self, LENS=[64, 64, 65, 67]):
        u = self.u
        frames = [[x & 0xff for x in range(1, L + 1)] for L in LENS]
        self.randomize(u.phy_tx)
        for f in frames:
            axis_send_bytes(u.eth.tx, f)
        len_sum = sum(LENS)
        self.runSim(CLK_PERIOD * (len_sum * 2 + 10))
        for f_ref in frames:
            f = self.pop_tx_frame()
            self.assertEqual(f[0], 0)  # frame offset
            f = f[1]

            self.assertEqual(len(f), len(f_ref) + 4)
            data = f[:-4]
            self.assertValSequenceEqual(data, f_ref)

            crc = f[-4:]
            crc_ref = crc32(bytes(data))
            crc = byte_list_to_be_int(crc)
            self.assertEqual(
                crc, crc_ref,
                "0x{0:8x} 0x{1:8x}".format(crc, crc_ref))
        self.assertEmpty(u.phy_tx._ag.data)


class EthernetMacTx_32b_TC(EthernetMacTx_8b_TC):
    DW = 32


class EthernetMacTx_64b_TC(EthernetMacTx_8b_TC):
    DW = 64


EthernetMac_tx_TCs = [
    EthernetMacTx_8b_TC,
    EthernetMacTx_32b_TC,
    EthernetMacTx_64b_TC,
]


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(EthernetMacTx_32b_TC('test_single'))
    for tc in EthernetMac_tx_TCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
