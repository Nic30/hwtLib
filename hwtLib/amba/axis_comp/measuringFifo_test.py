#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from random import Random
import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import agent_randomize
from hwtLib.amba.axis_comp.measuringFifo import AxiS_measuringFifo
from hwt.bitmask import mask


class AxiS_measuringFifoTC(SimTestCase):
    def setUp(self):
        super(AxiS_measuringFifoTC, self).setUp()
        u = self.u = AxiS_measuringFifo()
        self.MAX_LEN = 15
        u.MAX_LEN.set(self.MAX_LEN)
        u.SIZES_BUFF_DEPTH.set(4)
        
        self.prepareUnit(self.u)

    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)

        self.assertEqual(len(u.sizes._ag.data), 0)
        self.assertEqual(len(u.dataOut._ag.data), 0)

    def test_singleWordPacket(self):
        u = self.u

        u.dataIn._ag.data.extend([
                                  (2, mask(8), 1),
                                 ])

        self.doSim(200 * Time.ns)
        self.assertEqual(len(u.sizes._ag.data), 1)
        self.assertEqual(len(u.dataOut._ag.data), 1)

    def test_singleWordPacketWithDelay(self):
        u = self.u

        u.dataIn._ag.data.extend([(2, mask(8), 1),
                                  ])
        u.dataOut._ag.enable = False

        self.doSim(200 * Time.ns)
        self.assertEqual(len(u.sizes._ag.data), 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)
        self.assertValEqual(self.model.dataOut_last, 1)

    def test_multiplePackets(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        u.dataIn._ag.data.extend([(1, mask(8), 1),
                                  (2, mask(8), 1),
                                  (3, mask(8), 1)
                                  ])

        self.doSim(200 * Time.ns)
        self.assertEqual(len(sizes), 3)
        self.assertEqual(len(data), 3)
        self.assertValSequenceEqual(sizes, (8, 8, 8))

    def test_doubleWordPacket(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        u.dataIn._ag.data.extend([
                                  (1, mask(8), 0),
                                  (2, mask(8), 1)
                                 ])

        self.doSim(200 * Time.ns)
        self.assertEqual(len(sizes), 1)
        self.assertEqual(len(data), 2)
        self.assertValSequenceEqual(sizes, (16,))

    def test_withPause(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        u.dataIn._ag.data.extend([
                                  (i+1, 255, int(i==5)) for i in range(6)
                                 ])

        def pause(simulator):
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.enable = False
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.enable = True

        self.procs.append(pause)

        self.doSim(200 * Time.ns)

        self.assertEqual(len(sizes), 1)
        self.assertEqual(len(data), 6)
        self.assertValEqual(sizes[0], 6 * 8)

    def test_unalignedPacket(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        u.dataIn._ag.data.extend([
                                  (1, mask(8), 0),
                                  (2, mask(1), 1)
                                 ])
        self.doSim(200 * Time.ns)
        self.assertEqual(len(sizes), 1)
        self.assertEqual(len(data), 2)
        self.assertValSequenceEqual(sizes, (9,))

    def test_unalignedPacket1Word(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        u.dataIn._ag.data.extend([
                                  (2, 1, 1),
                                 ])
        self.doSim(200 * Time.ns)
        self.assertEqual(len(sizes), 1)
        self.assertEqual(len(data), 1)
        self.assertValSequenceEqual(sizes, (1,))

    def test_randomized(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data
        N = 30

        for i in range(N):
            u.dataIn._ag.data.extend([
                                      (i+1, mask(8), i==5) for i in range(6)
                                     ])
        self.randomize(u.dataIn)
        self.randomize(u.dataOut)
        self.randomize(u.sizes)

        self.doSim(N * 6 * 10 * 3 * Time.ns)

        self.assertEqual(len(sizes), N)
        self.assertEqual(len(data), N * 6)
        for s in sizes:
            self.assertValEqual(s, 6 * 8)

    def test_randomized10(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data
        N = 10
        expectedData = []
        expectedLen = []

        for i in range(N):
            l = int(self._rand.random() * (self.MAX_LEN+1+1))
            d = [(i + 1, mask(8), int(i == (l - 1))) for i in range(l)]
            u.dataIn._ag.data.extend(d)

            expectedData.extend(d)
            expectedLen.append(l * 8)

        self.randomize(u.dataIn)
        self.randomize(u.dataOut)
        self.randomize(u.sizes)

        self.doSim(len(expectedData) * 40 * Time.ns)

        self.assertEqual(len(sizes), N)
        self.assertEqual(len(data), len(expectedData))

        for exp, d in zip(expectedData, data):
            self.assertValSequenceEqual(d, exp)

        for el, l in zip(expectedLen, sizes):
            self.assertValEqual(l, el)

    def test_withSizeBrake(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data
        N = 30
        SIZE_BUFF_SIZE = 16
        L = 6
        expectedLen = []

        for i in range(N):
            d = [(i + 1, 255, int(i == (L - 1))) for i in range(L)]
            u.dataIn._ag.data.extend(d)
            expectedLen.append(L*8)

        self.randomize(u.dataIn)
        self.randomize(u.dataOut)
        u.sizes._ag.enable = False

        def sizesEn(s):
            yield s.wait((SIZE_BUFF_SIZE + 5) * 10 * Time.ns)
            yield from agent_randomize(u.sizes._ag, 
                                       50*Time.ns, 
                                       self._rand.getrandbits(64))(s)

        self.procs.append(sizesEn)

        self.doSim(N * 6 * 10 * 3 * Time.ns)

        self.assertEqual(len(sizes), N)
        self.assertEqual(len(data), N * 6)
        for el, l in zip(expectedLen, sizes):
            self.assertValEqual(l, el)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(AxiS_measuringFifoTC('test_withPause'))
    suite.addTest(unittest.makeSuite(AxiS_measuringFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
