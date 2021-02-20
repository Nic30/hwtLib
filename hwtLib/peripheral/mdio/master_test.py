from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.mdio.intf import Mdio
from hwtLib.peripheral.mdio.master import MdioMaster
from hwtSimApi.constants import Time


class MdioMasterTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = MdioMaster()
        u.FREQ = int(10e6)
        cls.MDIO_CLK = int((1e9 / u.MDIO_FREQ) * Time.ns)
        cls.compileSim(u)

    def test_nop(self):
        MDIO_CLK = self.MDIO_CLK
        self.runSim(MDIO_CLK * 64)

    def test_read(self):
        MDIO_CLK = self.MDIO_CLK
        u = self.u
        # opcode, (phyaddr, regaddr), wdata
        addr = (0x1, 0x13)
        MAGIC = 0xab12
        u.md._ag.data[addr] = MAGIC
        u.req._ag.data.append((Mdio.OP.READ, addr, None))
        self.runSim(MDIO_CLK * 100)

        self.assertValSequenceEqual(u.rdata._ag.data, [MAGIC, ])

    def test_write(self):
        MDIO_CLK = self.MDIO_CLK
        u = self.u
        # opcode, (phyaddr, regaddr), wdata
        addr = (0x1, 0x13)
        MAGIC = 0xab12
        u.md._ag.data[addr] = MAGIC
        u.req._ag.data.append((Mdio.OP.WRITE, addr, MAGIC))
        self.runSim(MDIO_CLK * 100)

        self.assertValEqual(u.md._ag.data[addr], MAGIC)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(MdioMasterTC('test_write'))
    suite.addTest(unittest.makeSuite(MdioMasterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)