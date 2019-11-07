#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hwt.synthesizer.utils import toRtl
from hwtLib.peripheral.spi.intf import Spi
from hwtLib.tests.statementTrees import StatementTreesTC


class EmptyUnitWithSpi(EmptyUnit):
    def _declr(self):
        self.spi = Spi()

expectedVhdl = """
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY EmptyUnitWithSpi IS
    GENERIC (spi_SLAVE_CNT: string := "1"
    );
    PORT (spi_clk: IN STD_LOGIC;
        spi_cs: IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        spi_miso: OUT STD_LOGIC;
        spi_mosi: IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF EmptyUnitWithSpi IS
BEGIN
    spi_miso <= 'X';
END ARCHITECTURE;
"""


class EmptyUnitWithSpiTC(unittest.TestCase):
    def test_vhdl(self):
        vhdl = toRtl(EmptyUnitWithSpi())
        StatementTreesTC.strStructureCmp(self, expectedVhdl, vhdl)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(EmptyUnitWithSpiTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    print(toRtl(EmptyUnitWithSpi()))
