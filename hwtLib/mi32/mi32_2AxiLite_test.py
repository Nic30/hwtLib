from hwt.hdl.constants import READ, WRITE
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axiLite_comp.denseMem import Axi4LiteDenseMem
from hwtLib.mi32.mi32_2AxiLite import Mi32_2AxiLite
from pyMathBitPrecise.bit_utils import mask
from pycocotb.agents.clk import DEFAULT_CLOCK


class Mi32_2AxiLiteTC(SingleUnitSimTestCase):
    def randomize_all(self):
        u = self.u
        self.randomize(u.s.ar)
        self.randomize(u.s.aw)
        self.randomize(u.s.r)
        self.randomize(u.s.w)
        self.randomize(u.s.b)

    @classmethod
    def getUnit(cls):
        u = cls.u = Mi32_2AxiLite()
        u.ADDR_WIDTH = u.DATA_WIDTH = 32
        return u

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        u = self.u
        self.memory = Axi4LiteDenseMem(u.clk, axi=u.s)
        self.randomize_all()

    def test_read(self):
        u = self.u
        N = 10
        addr_req = [(READ, i * 0x4) for i in range(N)]
        for i in range(N):
            self.memory.data[i] = i + 1
        u.m._ag.req.extend(addr_req)

        self.runSim(12 * N * DEFAULT_CLOCK)

        data = [i + 1 for i in range(N)]
        self.assertValSequenceEqual(u.m._ag.rData, data)

    def test_write(self):
        u = self.u
        m = mask(32 // 8)
        N = 10
        addr_req = [(WRITE, i * 0x4, 1 + i, m) for i in range(N)]
        u.m._ag.req.extend(addr_req)

        self.runSim(12 * N * DEFAULT_CLOCK)
        self.assertEmpty(u.m._ag.rData)
        ref_data = [i + 1 for i in range(N)]
        data = [self.memory.data[i] for i in range(N)]
        self.assertValSequenceEqual(data, ref_data)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(Mi32_2AxiLiteTC('test_write'))
    suite.addTest(unittest.makeSuite(Mi32_2AxiLiteTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
