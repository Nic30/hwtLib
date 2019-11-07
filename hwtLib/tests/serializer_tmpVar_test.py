import unittest

from hwt.code import connect
from hwt.interfaces.std import VectSignal
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl

TmpVarExample_asVhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY TmpVarExample IS
    PORT (a: IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        b: OUT STD_LOGIC_VECTOR(31 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF TmpVarExample IS
BEGIN
    assig_process_b: PROCESS (a)
    VARIABLE tmpTypeConv: UNSIGNED(7 DOWNTO 0);
    BEGIN
    tmpTypeConv := UNSIGNED(a(7 DOWNTO 0)) + TO_UNSIGNED(4, 8);
        b <= X"0000000" & STD_LOGIC_VECTOR(tmpTypeConv(3 DOWNTO 0));
    END PROCESS;

END ARCHITECTURE;"""


class TmpVarExample(Unit):
    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)._m()

    def _impl(self):
        a = self.a[8:] + 4
        connect(a[4:], self.b, fit=True)


class Serializer_tmpVar_TC(unittest.TestCase):
    def test_add_to_slice_vhdl(self):
        s = toRtl(TmpVarExample(), serializer=VhdlSerializer)
        self.assertEqual(s, TmpVarExample_asVhdl)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(Serializer_tmpVar_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
