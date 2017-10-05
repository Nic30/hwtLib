import unittest
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.interfaces.std import VectSignal
from hwt.code import Switch
from hwt.synthesizer.shortcuts import toRtl
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX, \
    ResourceLatch


class LatchInSwitch(Unit):
    def _declr(self):
        self.a = VectSignal(4)
        self.b = VectSignal(4)

    def _impl(self):
        Switch(self.a).addCases([(i, self.b(i)) for i in range(6)])
    
    
class ResourceAnalyzer_TC(unittest.TestCase):
    def test_latch_in_switch(self):
        u = LatchInSwitch()
        ra = ResourceAnalyzer()
        toRtl(u, serializer=ra)
        res = ra.report()
        expected = {
            (ResourceMUX, 4, 6): 1,
            ResourceLatch: 4
            }
        self.assertDictEqual(res, expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(ResourceAnalyzer_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
