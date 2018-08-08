#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import copy
import unittest

from hwt.hdl.constants import NOP
from hwt.interfaces.std import Handshaked
from hwt.simulator.simTestCase import SimTestCase

from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.mem.fifo_test import FifoTC


class HsFifoTC(FifoTC):

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u = HandshakedFifo(Handshaked)
        u.DEPTH.set(self.ITEMS)
        u.DATA_WIDTH.set(8)
        u.EXPORT_SIZE.set(True)
        self.prepareUnit(u)

    def getFifoItems(self):
        v = self.model.fifo_inst.memory._val.val.values()
        items = set([int(x) for x in v])
        items.add(int(self.model.dataOut_data._val))
        return items

    def getUnconsumedInput(self):
        d = copy(self.u.dataIn._ag.data)
        ad = self.u.dataIn._ag.actualData
        if ad != NOP:
            d.appendleft(ad)
        return d

    def test_stuckedData(self):
        super(HsFifoTC, self).test_stuckedData()
        self.assertValEqual(self.model.dataOut_data, 1)

    def test_tryMore2(self, capturedOffset=1):
        # capturedOffset=1 because handshaked aget can act in same clk
        super(HsFifoTC, self).test_tryMore2(capturedOffset=capturedOffset)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsFifoTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
