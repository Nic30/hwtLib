#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.hdl.types.bits import Bits


class SimpleUnitWithParam(Unit):
    """
    Simple parametrized unit.

    .. hwt-schematic::
    """
    def _config(self):
        # declaration of parameter DATA_WIDTH with default value 8
        # type of parameter is determined from used value
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        # first parameter of Bits HDL type constructor is width, second optional is signed flag
        dt = Bits(self.DATA_WIDTH)
        # dt is now type vector with width specified by parameter DATA_WIDTH
        # it means it is 8bit width we specify data type for every signal
        self.a = Signal(dtype=dt)
        # you can also use shortcut VectorSignal(width)
        self.b = Signal(dtype=dt)._m()

    def _impl(self):
        self.b(self.a)


class SimpleUnitWithParamTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls) -> Unit:
        u = SimpleUnitWithParam()
        u.DATA_WIDTH = 32
        return u

    def test_simple(self):
        u = self.u
        self.assertEqual(u.DATA_WIDTH, 32)
        self.assertEqual(u.a._dtype.bit_length(), 32)
        self.assertEqual(u.b._dtype.bit_length(), 32)

    # def test_canNotSetAfterSynth(self):
    #     u = SimpleUnitWithParam()
    #     self.compileSim(u)
    # 
    #     # with self.assertRaises(AssertionError, msg="Can not set after it was synthetized"):
    #     #     u.DATA_WIDTH = 32


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = SimpleUnitWithParam()

    # we can now optionally set our parameter to any chosen value
    u.DATA_WIDTH = 1024

    print(toRtl(u))

    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(SimpleUnitWithParamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

#  expected result
# --
# --    Simple parametrized unit.
# --
# library IEEE;
# use IEEE.std_logic_1164.all;
# use IEEE.numeric_std.all;
#
# ENTITY SimpleUnitWithParam IS
#     GENERIC (
#         DATA_WIDTH : INTEGER := 1024
#     );
#     PORT (a : IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
#         b : OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0)
#     );
# END ENTITY;
#
# ARCHITECTURE rtl OF SimpleUnitWithParam IS
#
#
#
# BEGIN
#
#     b <= a;
#
# END ARCHITECTURE;

# ...
