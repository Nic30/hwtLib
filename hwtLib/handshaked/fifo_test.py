#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.fifo import HandshakedFifo


class HsFifoTC(SimTestCase):
    def setUp(self):
        u = self.u = HandshakedFifo(Handshaked)
        u.DEPTH.set(8)
        u.DATA_WIDTH.set(4)
        u.EXPORT_SIZE.set(True)
        self.prepareUnit(u)

    def test_nop(self):
        u = self.u
        self.runSim(120 * Time.ns)
        self.assertEqual(len(u.dataOut._ag.data), 0)

    def test_stuckedData(self):
        u = self.u
        u.dataIn._ag.data.append(1)

        u.dataOut._ag._enabled = False
        self.runSim(120 * Time.ns)
        self.assertValEqual(self.model.dataOut_data, 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)

    def test_withPause(self):
        u = self.u
        golden = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        u.dataIn._ag.data.extend(golden)

        def pause(simulator):
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.setEnable_asMonitor(False, simulator)
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.setEnable_asMonitor(True, simulator)
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataIn._ag.setEnable_asDriver(False, simulator)
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataIn._ag.setEnable_asDriver(True, simulator)

        self.procs.append(pause)

        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, golden)
        self.assertSequenceEqual(u.dataIn._ag.data, [])

    def test_withPause2(self):
        u = self.u
        golden = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        u.dataIn._ag.data.extend(golden)

        def pause(simulator):
            yield simulator.wait(4 * 10 * Time.ns)
            u.dataOut._ag.setEnable_asMonitor(False, simulator)
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.setEnable_asMonitor(True, simulator)
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataIn._ag.setEnable_asDriver(False, simulator)
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataIn._ag.setEnable_asDriver(True, simulator)

        self.procs.append(pause)

        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, golden)
        self.assertSequenceEqual(u.dataIn._ag.data, [])

    def test_passdata(self):
        u = self.u
        golden = [1, 2, 3, 4, 5, 6]
        u.dataIn._ag.data.extend(golden)

        self.runSim(120 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, golden)
        self.assertValSequenceEqual(u.dataIn._ag.data, [])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsFifoTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
