#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.iLvl.simpleAxiStream import SimpleUnitAxiStream
from hwt.simulator.simTestCase import SimTestCase
from hwt.hdlObjects.constants import Time
from hwt.interfaces.utils import addClkRstn, propagateClkRstn


class SimpleSubunit2(Unit):
    def _declr(self):
        addClkRstn(self)
        self.subunit0 = SimpleUnitAxiStream()
        self.a0 = AxiStream()
        self.b0 = AxiStream()

        self.a0.DATA_WIDTH.set(8)
        self.b0.DATA_WIDTH.set(8)

    def _impl(self):
        propagateClkRstn(self)
        u = self.subunit0
        u.a ** self.a0
        self.b0 ** u.b
        
        

class SimpleSubunit2TC(SimTestCase):
    def test_simplePass(self):
        u = SimpleSubunit2()
        self.prepareUnit(u)

        data = [(5, 1, 0), (6, 1, 1)]
        u.a0._ag.data.extend(data)
        self.doSim(50 * Time.ns)
        
        self.assertValSequenceEqual(u.b0._ag.data, data)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleSubunit2()))

    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SimpleSubunit2TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)