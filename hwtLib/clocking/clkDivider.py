#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.constants import Time
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Clk
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit


class ClkDiv3(Unit):
    """
    :attention: this clock divider implementation suits well for generating of slow output clock
        inside fpga you should use clocking primitives
        (http://www.xilinx.com/support/documentation/ip_documentation/clk_wiz/v5_1/pg065-clk-wiz.pdf)

    .. hwt-schematic::
    """
    def _declr(self):
        addClkRstn(self)
        self.clkOut = Clk()._m()

    def _impl(self):
        clk = self.clk
        r_cnt = self._sig("r_cnt", Bits(2))
        f_cnt = self._sig("f_cnt", Bits(2))
        rise = self._sig("rise")
        fall = self._sig("fall")
        CNTR_MAX = 2

        If(self.rst_n._isOn(),
           r_cnt(CNTR_MAX),
           rise(1),
           f_cnt(1),
           fall(0)
        ).Else(
            If(clk._onRisingEdge(),
                If(r_cnt._eq(CNTR_MAX),
                    r_cnt(0),
                    rise(~rise)
                ).Else(
                    r_cnt(r_cnt + 1),
                )
            ),
            If(clk._onFallingEdge(),
                If(f_cnt._eq(CNTR_MAX),
                    f_cnt(0),
                    fall(~fall)
                ).Else(
                    f_cnt(f_cnt + 1),
                )
            )
        )

        self.clkOut((r_cnt != CNTR_MAX) & (f_cnt != CNTR_MAX))  # fall._eq(rise)


class ClkDiv3TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = ClkDiv3()
        return cls.u

    def test_oscilation(self):
        self.runSim(10 * 10 * Time.ns)
        expected = [(0, 0),
                    (20000.0, 1),
                    (35000.0, 0),
                    (50000.0, 1),
                    (65000.0, 0),
                    (80000.0, 1),
                    (95000.0, 0)]
        self.assertValSequenceEqual(self.u.clkOut._ag.data,
                                    expected)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(ClkDiv3()))

    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(ClkDiv3TC('test_oscilation'))
    suite.addTest(unittest.makeSuite(ClkDiv3TC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
