from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.mdio.intf import Mdio
from hwtLib.peripheral.mdio.master import MdioMaster
from hwtSimApi.constants import Time


class MdioMasterTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = MdioMaster()
        dut.FREQ = int(10e6)
        cls.MDIO_CLK = int((1e9 / dut.MDIO_FREQ) * Time.ns)
        cls.compileSim(dut)

    def test_nop(self):
        MDIO_CLK = self.MDIO_CLK
        self.runSim(MDIO_CLK * 64)

    def test_read(self):
        MDIO_CLK = self.MDIO_CLK
        dut = self.dut
        # opcode, (phyaddr, regaddr), wdata
        addr = (0x1, 0x13)
        MAGIC = 0xab12
        dut.md._ag.data[addr] = MAGIC
        dut.req._ag.data.append((Mdio.OP.READ, addr, None))
        self.runSim(MDIO_CLK * 100)

        self.assertValSequenceEqual(dut.rdata._ag.data, [MAGIC, ])

    def test_write(self):
        MDIO_CLK = self.MDIO_CLK
        dut = self.dut
        # opcode, (phyaddr, regaddr), wdata
        addr = (0x1, 0x13)
        MAGIC = 0xab12
        dut.md._ag.data[addr] = MAGIC
        dut.req._ag.data.append((Mdio.OP.WRITE, addr, MAGIC))
        self.runSim(MDIO_CLK * 100)

        self.assertValEqual(dut.md._ag.data[addr], MAGIC)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([MdioMasterTC("test_write")])
    suite = testLoader.loadTestsFromTestCase(MdioMasterTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)