#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.interfaces.std import VldSynced
from hwt.serializer.ipCoreWrapper import IpCoreWrapper
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
from hwtLib.samples.ipCoreCompatibleWrap import ArrayIntfExample


UnitWithParams_in_wrap_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY baseUnit IS
    GENERIC (DATA_WIDTH: INTEGER := 64;
        din_DATA_WIDTH: INTEGER := 64;
        dout_DATA_WIDTH: INTEGER := 64
    );
    PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
        din_vld: IN STD_LOGIC;
        dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
        dout_vld: OUT STD_LOGIC
    );
END baseUnit;

ARCHITECTURE rtl OF baseUnit IS
BEGIN
    dout_data <= din_data;
    dout_vld <= din_vld;
END ARCHITECTURE rtl;
--
--    Class which creates wrapper which converts all incompatible parts of unit
--    to ipcore compatible this means:
--
--    * convert array interface to multiple interfaces
--
--    original unit will be placed inside as subunit named baseUnit
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY UnitWithParams IS
    GENERIC (DATA_WIDTH: INTEGER := 64;
        baseUnit_din_DATA_WIDTH: INTEGER := 64;
        baseUnit_dout_DATA_WIDTH: INTEGER := 64
    );
    PORT (din_data: IN STD_LOGIC_VECTOR(baseUnit_din_DATA_WIDTH - 1 DOWNTO 0);
        din_vld: IN STD_LOGIC;
        dout_data: OUT STD_LOGIC_VECTOR(baseUnit_dout_DATA_WIDTH - 1 DOWNTO 0);
        dout_vld: OUT STD_LOGIC
    );
END UnitWithParams;

ARCHITECTURE rtl OF UnitWithParams IS
    SIGNAL sig_baseUnit_din_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_baseUnit_din_vld: STD_LOGIC;
    SIGNAL sig_baseUnit_dout_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_baseUnit_dout_vld: STD_LOGIC;
    COMPONENT baseUnit IS
       GENERIC (DATA_WIDTH: INTEGER := 64;
            din_DATA_WIDTH: INTEGER := 64;
            dout_DATA_WIDTH: INTEGER := 64
       );
       PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
            din_vld: IN STD_LOGIC;
            dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
            dout_vld: OUT STD_LOGIC
       );
    END COMPONENT;

BEGIN
    baseUnit_inst: COMPONENT baseUnit
        GENERIC MAP (DATA_WIDTH => 64,
            din_DATA_WIDTH => 64,
            dout_DATA_WIDTH => 64
        )
        PORT MAP (din_data => sig_baseUnit_din_data,
            din_vld => sig_baseUnit_din_vld,
            dout_data => sig_baseUnit_dout_data,
            dout_vld => sig_baseUnit_dout_vld
        );

    dout_data <= sig_baseUnit_dout_data;
    dout_vld <= sig_baseUnit_dout_vld;
    sig_baseUnit_din_data <= din_data;
    sig_baseUnit_din_vld <= din_vld;
END ARCHITECTURE rtl;"""


class UnitWithParams(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.din = VldSynced()
        self.dout = VldSynced()

    def _impl(self):
        self.dout(self.din)


class IpCoreWrapperTC(unittest.TestCase):
    def test_params_of_base_unit(self):
        u = UnitWithParams()
        w = IpCoreWrapper(u)
        s = toRtl(w, serializer=VhdlSerializer)
        self.assertEqual(s, UnitWithParams_in_wrap_vhdl)

    def test_interfaces(self):
        u = IpCoreWrapper(ArrayIntfExample())
        toRtl(u)
        self.assertTrue(hasattr(u, "a_0"))
        self.assertTrue(hasattr(u, "a_1"))
        self.assertFalse(hasattr(u, "a"))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IpCoreWrapperTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
