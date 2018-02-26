#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask, mask_bytes
from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.measuringFifo import AxiS_measuringFifo
from hwt.pyUtils.arrayQuery import take, iter_with_last


class AxiS_measuringFifoTC(SimTestCase):
    def setUp(self):
        super(AxiS_measuringFifoTC, self).setUp()
        u = self.u = AxiS_measuringFifo()
        self.DATA_WIDTH = 64
        self.MAX_LEN = 15

        u.MAX_LEN.set(self.MAX_LEN)
        u.SIZES_BUFF_DEPTH.set(4)
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u)

    def test_nop(self):
        u = self.u
        self.runSim(200 * Time.ns)

        self.assertEqual(len(u.sizes._ag.data), 0)
        self.assertEqual(len(u.dataOut._ag.data), 0)

    def test_singleWordPacket(self):
        u = self.u

        u.dataIn._ag.data.extend([
            (2, mask(8), 1),
        ])

        self.runSim(200 * Time.ns)
        self.assertValSequenceEqual(u.sizes._ag.data, [8, ])
        self.assertValSequenceEqual(u.dataOut._ag.data, [(2, mask(8), 1), ])

    def test_singleWordPacketWithDelay(self):
        u = self.u

        u.dataIn._ag.data.extend([(2, mask(8), 1),
                                  ])
        u.dataOut._ag._enabled = False

        self.runSim(200 * Time.ns)
        self.assertValSequenceEqual(u.sizes._ag.data, [8, ])
        self.assertEmpty(u.dataOut._ag.data, 0)
        self.assertValEqual(self.model.dataOut_last, 1)

    def test_multiplePackets(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        goldenData = [(1, mask(8), 1),
                      (2, mask(8), 1),
                      (3, mask(8), 1)
                      ]

        u.dataIn._ag.data.extend(goldenData)

        self.runSim(200 * Time.ns)
        self.assertValSequenceEqual(data, goldenData)
        self.assertValSequenceEqual(sizes, [8, 8, 8])

    def test_doubleWordPacket(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        goldenData = [(1, mask(8), 0),
                      (2, mask(8), 1)
                      ]
        u.dataIn._ag.data.extend(goldenData)

        self.runSim(200 * Time.ns)
        self.assertValSequenceEqual(data, goldenData)
        self.assertValSequenceEqual(sizes, (16,))

    def test_withPause(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        goldenData = [
            (i + 1, 255, int(i == 5)) for i in range(6)
        ]
        u.dataIn._ag.data.extend(goldenData)

        def pause(simulator):
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.setEnable_asMonitor(False, simulator)
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.setEnable_asMonitor(True, simulator)

        self.procs.append(pause)

        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(data, goldenData)
        self.assertValSequenceEqual(sizes, [6 * 8])

    def test_unalignedPacket(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        goldenData = [
            (1, mask(8), 0),
            (2, mask(1), 1)
        ]
        u.dataIn._ag.data.extend(goldenData)

        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(data, goldenData)
        self.assertValSequenceEqual(sizes, (9,))

    def test_unalignedPacket1Word(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data

        goldenData = [(2, 1, 1), ]
        u.dataIn._ag.data.extend(goldenData)

        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(data, goldenData)
        self.assertValSequenceEqual(sizes, (1,))

    def test_randomized(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data
        N = 30

        for i in range(N):
            u.dataIn._ag.data.extend([
                (i + 1, mask(8), i == 5) for i in range(6)
            ])
        self.randomize(u.dataIn)
        self.randomize(u.dataOut)
        self.randomize(u.sizes)

        self.runSim(N * 6 * 10 * 3 * Time.ns)

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
            _l = int(self._rand.random() * (self.MAX_LEN + 1 + 1))
            d = [(i + 1, mask(8), int(i == (_l - 1))) for i in range(_l)]
            u.dataIn._ag.data.extend(d)

            expectedData.extend(d)
            expectedLen.append(_l * 8)

        self.randomize(u.dataIn)
        self.randomize(u.dataOut)
        self.randomize(u.sizes)

        self.runSim(len(expectedData) * 30 * Time.ns)

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
            expectedLen.append(L * 8)

        self.randomize(u.dataIn)
        self.randomize(u.dataOut)
        u.sizes._ag.enable = False

        def sizesEn(sim):
            yield sim.wait((SIZE_BUFF_SIZE + 5) * 10 * Time.ns)
            yield from self.simpleRandomizationProcess(u.sizes._ag)(sim)

        self.procs.append(sizesEn)

        self.runSim(N * 6 * 10 * 3 * Time.ns)

        self.assertEqual(len(sizes), N)
        self.assertEqual(len(data), N * 6)
        for el, l in zip(expectedLen, sizes):
            self.assertValEqual(l, el)

    def sendFrame(self, data):
        u = self.u
        _mask = mask(self.DATA_WIDTH // 8)
        _d = [(d, _mask, int(i == (len(data) - 1)))
              for i, d in enumerate(data)]
        u.dataIn._ag.data.extend(_d)

    def getFrames(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = iter(u.dataOut._ag.data)
        size_of_word = self.DATA_WIDTH // 8

        frames = []
        for s in sizes:
            _s = int(s)
            words = _s // size_of_word
            if _s / size_of_word - words > 0.0:
                words += 1

            frame = []
            for last, (_d, _mask,  _last) in iter_with_last(take(data, words)):
                self.assertValEqual(_last, last)
                _mask = int(_mask)
                _d.val = mask_bytes(_d.val, _mask, size_of_word)
                _d.vldMask = mask_bytes(_d.vldMask, _mask, size_of_word)
                frame.append(int(_d))
            frames.append(frame)

        return frames

    def test_overflow(self):
        MAX_LEN = self.MAX_LEN
        data = [i for i in range(MAX_LEN + 4)]
        self.sendFrame(data)

        self.runSim((MAX_LEN + 10) * 10 * Time.ns)
        f = self.getFrames()
        self.assertEquals(f,
                          [[i for i in range(MAX_LEN + 1)],
                           [MAX_LEN + 1, MAX_LEN + 2, MAX_LEN + 3]])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_measuringFifoTC('test_singleWordPacket'))
    suite.addTest(unittest.makeSuite(AxiS_measuringFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
