#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream


class Simple2withNonDirectIntConnection(Unit):
    """
    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.USE_STRB = Param(True)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.a = AxiStream()
            self.c = AxiStream()._m()

    def _impl(self):
        # we have to register interface on this unit first before use
        with self._paramsShared():
            self.b = AxiStream()
        b = self.b

        b(self.a)
        self.c(b)


class Simple2withNonDirectIntConnectionTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls) -> Unit:
        u = Simple2withNonDirectIntConnection()
        return u

    def test_passData(self):
        u = self.u
        # (data, strb, last)
        u.a._ag.data.extend([
            (1, 1, 0),
            (2, 1, 1)
        ])
        self.runSim(100 * Time.ns)

        self.assertValSequenceEqual(u.c._ag.data, [
            (1, 1, 0),
            (2, 1, 1)
        ])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(Simple2withNonDirectIntConnectionTC('test_passData'))
    suite.addTest(unittest.makeSuite(Simple2withNonDirectIntConnectionTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synthesizer.utils import toRtl
    u = Simple2withNonDirectIntConnection()
    print(toRtl(u))
