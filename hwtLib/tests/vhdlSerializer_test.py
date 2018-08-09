import unittest

from hwt.code import Concat
from hwt.interfaces.std import VectSignal
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
from hwt.hdl.typeShortcuts import hBit, vec


TernaryInConcatExample_asVhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY TernaryInConcatExample IS
    PORT (a: IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        b: IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        c: OUT STD_LOGIC_VECTOR(31 DOWNTO 0)
    );
END TernaryInConcatExample;

ARCHITECTURE rtl OF TernaryInConcatExample IS
BEGIN
    assig_process_c: PROCESS (a, b)
    VARIABLE tmpTernary: STD_LOGIC;
    VARIABLE tmpTernary_0: STD_LOGIC;
    VARIABLE tmpTernary_1: STD_LOGIC;
    VARIABLE tmpTernary_2: STD_LOGIC;
    VARIABLE tmpTernary_3: STD_LOGIC;
    VARIABLE tmpTernary_4: STD_LOGIC;
    BEGIN
    IF a /= b THEN
        tmpTernary := '1';
    ELSE
        tmpTernary := '0';
    END IF;
    IF a < b THEN
        tmpTernary_0 := '1';
    ELSE
        tmpTernary_0 := '0';
    END IF;
    IF a <= b THEN
        tmpTernary_1 := '1';
    ELSE
        tmpTernary_1 := '0';
    END IF;
    IF a = b THEN
        tmpTernary_2 := '1';
    ELSE
        tmpTernary_2 := '0';
    END IF;
    IF a >= b THEN
        tmpTernary_3 := '1';
    ELSE
        tmpTernary_3 := '0';
    END IF;
    IF a > b THEN
        tmpTernary_4 := '1';
    ELSE
        tmpTernary_4 := '0';
    END IF;
        c <= X"f" & tmpTernary & tmpTernary_0 & tmpTernary_1 & tmpTernary_2 & tmpTernary_3 & tmpTernary_4 & "0000000000000000000000";
    END PROCESS;

END ARCHITECTURE rtl;"""


class TernaryInConcatExample(Unit):
    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)
        self.c = VectSignal(32)

    def _impl(self):
        a = self.a
        b = self.b
        self.c(
            Concat(
                hBit(1),
                vec(7, 3),
                a != b,
                a < b,
                a <= b,
                a._eq(b),
                a >= b,
                a > b,
                vec(0, 22),
                )
            )


class VhdlSerializer_TC(unittest.TestCase):
    def test_add_to_slice_vhdl(self):
        s = toRtl(TernaryInConcatExample(), serializer=VhdlSerializer)
        self.assertEqual(s, TernaryInConcatExample_asVhdl)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(VhdlSerializer_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
