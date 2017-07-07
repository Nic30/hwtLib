#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Signal
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit


class SimpleWithNonDirectIntConncetion(Unit):
    """
    Example of fact that interfaces does not have to be only extern
    the can be used even for connection inside unit
    """

    def _declr(self):
        self.a = Signal()
        self.c = Signal()

    def _impl(self):
        self.b = Signal()

        self.b ** self.a
        self.c ** self.b


class SimpleWithNonDirectIntConncetionTC(SimTestCase):
    def test_passData(self):
        u = SimpleWithNonDirectIntConncetion()
        self.prepareUnit(u)
        d = [0, 1, 0, 1, 0]
        u.a._ag.data.extend(d)
        self.doSim(100 * Time.ns)
        self.assertValSequenceEqual(u.c._ag.data, d)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(SimpleWithNonDirectIntConncetionTC('test_passData'))
    suite.addTest(unittest.makeSuite(SimpleWithNonDirectIntConncetionTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleWithNonDirectIntConncetion()))
