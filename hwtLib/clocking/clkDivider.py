#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Clk
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.simulator.simTestCase import SimTestCase
from hwt.hdlObjects.constants import Time


class ClkDiv3(Unit):
    """
    :attention: this clock divider implementation suits well for generating of slow output clock
        inside fpga you should use clocking primitives
        (http://www.xilinx.com/support/documentation/ip_documentation/clk_wiz/v5_1/pg065-clk-wiz.pdf)
    """
    def _declr(self):
        addClkRstn(self)
        self.clkOut = Clk()

    def _impl(self):
        clk = self.clk
        r_cnt = self._sig("r_cnt", vecT(2))
        f_cnt = self._sig("f_cnt", vecT(2))
        rise = self._sig("rise")
        fall = self._sig("fall")
        CNTR_MAX = 2


        If(self.rst_n._isOn(),
           r_cnt ** 0,
           rise ** 1,
           f_cnt ** CNTR_MAX,
           fall ** 1
        ).Else(
            If(clk._onRisingEdge(),
                If(r_cnt._eq(CNTR_MAX),
                    r_cnt ** 0,
                    rise ** ~rise
                ).Else(
                    r_cnt ** (r_cnt + 1),
                )
            ),
            If(clk._onFallingEdge(),
                If(f_cnt._eq(CNTR_MAX),
                    f_cnt ** 0,
                    fall ** ~fall
                ).Else(
                    f_cnt ** (f_cnt + 1),
                )
            )
        )

        self.clkOut ** ((r_cnt != CNTR_MAX) & (f_cnt != CNTR_MAX))  # fall._eq(rise)


class ClkDiv3TC(SimTestCase):
    def test_oscilation(self):
        u = ClkDiv3()
        self.prepareUnit(u)

        self.doSim(10 * 10 * Time.ns)
        expected = [(0, 0),
                    (15000.0, 1),
                    (30000.0, 0),
                    (45000.0, 1),
                    (60000.0, 0),
                    (75000.0, 1),
                    (90000.0, 0)]
        self.assertValSequenceEqual(u.clkOut._ag.data,
                                    expected)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(ClkDiv3()))

    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(ClkDiv3TC('test_oscilation'))
    suite.addTest(unittest.makeSuite(ClkDiv3TC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
