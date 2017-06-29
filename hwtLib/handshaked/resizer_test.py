from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.pyUtils.arrayQuery import grouper
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.resizer_test import it
from hwtLib.handshaked.resizer import HsResizer


class HsResizerTC(SimTestCase):
    def test_1to1(self):
        u = HsResizer(Handshaked, [1, 1],
                      lambda intf: intf.DATA_WIDTH.set(32),
                      lambda intf: intf.DATA_WIDTH.set(32))
        self.prepareUnit(u)
        # self.randomize(u.dataIn)
        # self.randomize(u.dataOut)
        N = 10

        d = [self._rand.getrandbits(32) for _ in range(N)]

        u.dataIn._ag.data.extend(d)

        self.doSim(N * 40 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, d)

    def test_1to3(self):
        u = HsResizer(Handshaked, [1, 3],
                      lambda intf: intf.DATA_WIDTH.set(32),
                      lambda intf: intf.DATA_WIDTH.set(3 * 32))
        self.prepareUnit(u)
        # self.randomize(u.dataIn)
        # self.randomize(u.dataOut)
        N = 9

        d = [self._rand.getrandbits(32) for _ in range(N)]

        u.dataIn._ag.data.extend(d)

        self.doSim(N * 40 * Time.ns)

        expected = []
        for a, b, c in grouper(3, d):
            v = it(32, a, b, c)
            expected.append(v)

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)

    def test_3to1(self):
        u = HsResizer(Handshaked, [3, 1],
                      lambda intf: intf.DATA_WIDTH.set(3 * 32),
                      lambda intf: intf.DATA_WIDTH.set(32))
        self.prepareUnit(u)
        # self.randomize(u.dataIn)
        # self.randomize(u.dataOut)
        N = 9

        d = [self._rand.getrandbits(3 * 32) for _ in range(N)]

        u.dataIn._ag.data.extend(d)

        self.doSim(3 * N * 40 * Time.ns)

        expected = []
        m = mask(32)
        for a in d:
            expected.extend([a & m, (a >> 32) & m, (a >> 64) & m])

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    #suite.addTest(HandshakedResizerTC('test_1to3'))
    suite.addTest(unittest.makeSuite(HsResizerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
