from hwt.hdl.constants import READ
from hwt.interfaces.std import BramPort_withoutClk
from hwt.interfaces.utils import addClkRst
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwtSimApi.constants import CLK_PERIOD


class BramWire(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRst(self)
        self.din = BramPort_withoutClk()
        self.dout = BramPort_withoutClk()._m()

    def _impl(self):
        self.dout(self.din)


class BramWireTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = BramWire()
        cls.compileSim(cls.u)

    def test_read(self):
        u = self.u
        u.dout._ag.mem[1] = 1
        u.dout._ag.mem[2] = 2

        u.din._ag.requests.extend([(READ, 1), (READ, 2), (READ, 3)])
        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(u.din._ag.r_data, [1, 2, None])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(RamTC('test_async_resources'))
    suite.addTest(unittest.makeSuite(BramWireTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
