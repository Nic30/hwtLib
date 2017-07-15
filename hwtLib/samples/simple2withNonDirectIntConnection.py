#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream


class Simple2withNonDirectIntConnection(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.a = AxiStream()
            self.c = AxiStream()

    def _impl(self):
        # we have to register interface on this unit first before use
        with self._paramsShared():
            self.b = AxiStream()
        b = self.b

        b ** self.a
        self.c ** b


class Simple2withNonDirectIntConnectionTC(SimTestCase):
    def test_passData(self):
        u = Simple2withNonDirectIntConnection()
        self.prepareUnit(u)

        # (data, strb, last)
        u.a._ag.data.extend([
            (1, 1, 0),
            (2, 1, 1)
            ])
        self.doSim(100 * Time.ns)

        self.assertValSequenceEqual(u.c._ag.data,
            [
            (1, 1, 0),
            (2, 1, 1)
            ])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(Simple2withNonDirectIntConnectionTC('test_passData'))
    suite.addTest(unittest.makeSuite(Simple2withNonDirectIntConnectionTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(Simple2withNonDirectIntConnection))
