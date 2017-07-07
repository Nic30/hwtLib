#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.typeShortcuts import hInt
from hwt.interfaces.std import VldSynced
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param


class InterfaceArraySample0(Unit):
    """
    Sample unit with array interface (a and b)
    which is not using items of these array interfaces
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.LEN = hInt(3)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.a = VldSynced(asArraySize=self.LEN)
            self.b = VldSynced(asArraySize=self.LEN)

    def _impl(self):
        # directly connect arrays, note that we are not using array items
        # and thats why they are not created
        self.b ** self.a


class InterfaceArraySample0TC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        self.u = InterfaceArraySample0()
        self.prepareUnit(self.u)

    def test_simplePass(self):
        u = self.u

        u.a[0]._ag.data.extend([1, 2, 3])
        u.a[1]._ag.data.extend([9])
        u.a[2]._ag.data.extend([10, 11, 12, 13])

        self.doSim(50 * Time.ns)

        for i in range(3):
            self.assertEmpty(u.a[i]._ag.data)

        self.assertValSequenceEqual(u.b[0]._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(u.b[1]._ag.data, [9])
        self.assertValSequenceEqual(u.b[2]._ag.data, [10, 11, 12, 13])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Simple2withNonDirectIntConnectionTC('test_passData'))
    suite.addTest(unittest.makeSuite(InterfaceArraySample0TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(InterfaceArraySample0()))
