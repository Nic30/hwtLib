#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import copy
import unittest

from hwt.hdl.constants import NOP
from hwt.interfaces.std import Handshaked

from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.mem.fifo_test import FifoTC


class HsFifoTC(FifoTC):

    @classmethod
    def getUnit(cls):
        u = cls.u = HandshakedFifo(Handshaked)
        u.DEPTH = cls.ITEMS
        u.DATA_WIDTH = 64
        u.EXPORT_SIZE = True
        return u

    def getFifoItems(self):
        m = self.rtl_simulator.model
        v = m.fifo_inst.io.memory
        items = set([int(x.read()) for x in v])
        items.add(int(m.io.dataOut_data.read()))
        return items

    def getUnconsumedInput(self):
        d = copy(self.u.dataIn._ag.data)
        ad = self.u.dataIn._ag.actualData
        if ad != NOP:
            d.appendleft(ad)
        return d

    def test_stuckedData(self):
        super(HsFifoTC, self).test_stuckedData()
        self.assertValEqual(self.rtl_simulator.io.dataOut_data, 1)

    def test_tryMore2(self, capturedOffset=1):
        # capturedOffset=1 because handshaked aget can act in same clk
        super(HsFifoTC, self).test_tryMore2(capturedOffset=capturedOffset)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsFifoTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
