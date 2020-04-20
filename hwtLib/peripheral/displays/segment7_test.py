#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.synthesizer.utils import toRtl
from hwtLib.peripheral.segment7 import Segment7
from hwt.serializer.vhdl.serializer import VhdlSerializer

segment7_vhdl = """--
--    7-segment display decoder
--
--    :note: led in display becomes active when output = 0
--
--    Display pin connection on image below.
--
--    .. code-block:: raw
--
--        -------------
--        |     0     |
--        -------------
--        | 5 |   | 1 |
--        -------------
--        |     6     |
--        -------------
--        | 4 |   | 2 |
--        -------------
--        |     3     |
--        -------------
--
--    .. hwt-schematic::
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY Segment7 IS
    PORT (dataIn: IN STD_LOGIC_VECTOR(3 DOWNTO 0);
        dataOut: OUT STD_LOGIC_VECTOR(6 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF Segment7 IS
BEGIN
    assig_process_dataOut: PROCESS (dataIn)
    BEGIN
        CASE dataIn IS
        WHEN X"0" =>
            dataOut <= "0000001";
        WHEN X"1" =>
            dataOut <= "1001111";
        WHEN X"2" =>
            dataOut <= "0010010";
        WHEN X"3" =>
            dataOut <= "0000110";
        WHEN X"4" =>
            dataOut <= "1001100";
        WHEN X"5" =>
            dataOut <= "0100100";
        WHEN X"6" =>
            dataOut <= "0100000";
        WHEN X"7" =>
            dataOut <= "0001111";
        WHEN X"8" =>
            dataOut <= "0000000";
        WHEN X"9" =>
            dataOut <= "0000100";
        WHEN OTHERS =>
            dataOut <= "1111111";
        END CASE;
    END PROCESS;

END ARCHITECTURE;"""


class Segment7TC(unittest.TestCase):
    def test_toVhdl(self):
        s = toRtl(Segment7(), serializer=VhdlSerializer)
        self.assertEqual(s, segment7_vhdl)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(OneHotToBinTC('test_basic'))
    suite.addTest(unittest.makeSuite(Segment7TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
