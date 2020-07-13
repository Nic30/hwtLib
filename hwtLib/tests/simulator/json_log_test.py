#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.rtlSimulatorJson import BasicRtlSimulatorJson
from hwtLib.handshaked.fifo_test import HsFifoTC


class HsFifoJsonLogTC(HsFifoTC):
    DEFAULT_SIMULATOR = BasicRtlSimulatorJson
    DEFAULT_LOG_DIR = None

    def runSim(self, until:float, name=None):
        data = {}
        self.rtl_simulator.set_trace_file(data, -1)
        return HsFifoTC.runSim(self, until, name=name)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsFifoJsonLogTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsFifoJsonLogTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
