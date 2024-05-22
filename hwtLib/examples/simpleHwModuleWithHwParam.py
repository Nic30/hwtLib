#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase


class SimpleHwModuleWithHwParam(HwModule):
    """
    Simple parametrized module.

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        # declaration of parameter DATA_WIDTH with default value 8
        # type of parameter is determined from used value
        self.DATA_WIDTH = HwParam(8)

    @override
    def hwDeclr(self):
        # first parameter of HBits HDL type constructor is width, second optional is signed flag
        dt = HBits(self.DATA_WIDTH)
        # dt is now type vector with width specified by parameter DATA_WIDTH
        # it means it is 8bit width we specify data type for every signal
        self.a = HwIOSignal(dtype=dt)
        # you can also use shortcut VectorSignal(width)
        self.b = HwIOSignal(dtype=dt)._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class SimpleHwModuleWithParamTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = SimpleHwModuleWithHwParam()
        dut.DATA_WIDTH = 32
        cls.compileSim(dut)

    def test_simple(self):
        dut = self.dut
        self.assertEqual(dut.DATA_WIDTH, 32)
        self.assertEqual(dut.a._dtype.bit_length(), 32)
        self.assertEqual(dut.b._dtype.bit_length(), 32)

    # def test_canNotSetAfterSynth(self):
    #     dut = SimpleHwModuleWithHwParam()
    #     self.compileSim(dut)
    #
    #     # with self.assertRaises(AssertionError, msg="Can not set after it was synthetized"):
    #     #     dut.DATA_WIDTH = 32


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = SimpleHwModuleWithHwParam()

    # we can now optionally set our parameter to any chosen value
    m.DATA_WIDTH = 1024

    print(to_rtl_str(m))

    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SimpleHwModuleWithParamTC("test_nothingEnable")])
    suite = testLoader.loadTestsFromTestCase(SimpleHwModuleWithParamTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

#  expected result
# LIBRARY IEEE;
# USE IEEE.std_logic_1164.ALL;
# USE IEEE.numeric_std.ALL;
# --
# --    Simple parametrized module.
# --
# --    .. hwt-autodoc::
# --
# ENTITY SimpleHwModuleWithHwParam IS
#     GENERIC(
#         DATA_WIDTH : INTEGER := 1024
#     );
#     PORT(
#         a : IN STD_LOGIC_VECTOR(1023 DOWNTO 0);
#         b : OUT STD_LOGIC_VECTOR(1023 DOWNTO 0)
#     );
# END ENTITY;
#
# ARCHITECTURE rtl OF SimpleHwModuleWithHwParam IS
# BEGIN
#     b <= a;
#     ASSERT DATA_WIDTH = 1024 REPORT "Generated only for this value" SEVERITY failure;
# END ARCHITECTURE;

# ...
