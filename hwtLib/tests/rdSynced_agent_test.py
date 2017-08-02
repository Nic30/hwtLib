import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import RdSynced
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit


class RdSyncedPipe(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = RdSynced()
        self.b = RdSynced()

    def _impl(self):
        self.b ** self.a


class RdSynced_agent_TC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        self.u = RdSyncedPipe()
        self.prepareUnit(self.u)

    def test_basic_data_pass(self):
        u = self.u

        u.a._ag.data.extend(range(10))

        self.doSim(150 * Time.ns)

        self.assertValSequenceEqual(u.b._ag.data, list(range(10)) + [None])


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(RdSynced_agent_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
