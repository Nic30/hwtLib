from hwt.hdl.constants import READ
from hwt.interfaces.std import BramPort_withoutClk
from hwt.interfaces.utils import addClkRst
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit
from pycocotb.agents.clk import DEFAULT_CLOCK


class BramWire(Unit):

    def _declr(self):
        addClkRst(self)
        self.din = BramPort_withoutClk()
        self.dout = BramPort_withoutClk()._m()

    def _impl(self):
        self.dout(self.din)


class BramWireTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls) -> Unit:
        cls.u = BramWire()
        return cls.u

    def test_read(self):
        u = self.u
        u.dout._ag.mem[1] = 1
        u.dout._ag.mem[2] = 2
        
        u.din._ag.requests.extend([(READ, 1), (READ, 2), (READ, 3)])
        
        self.runSim(10 * DEFAULT_CLOCK)
        
        self.assertValSequenceEqual(u.din._ag.readed, [1, 2, None])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(RamTC('test_async_resources'))
    suite.addTest(unittest.makeSuite(BramWireTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
