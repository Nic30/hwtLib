from io import StringIO
import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.builders.handshakedBuilderSimple import HandshakedBuilderSimple


class DumpTestbenchTC(SimTestCase):
    def test_passData(self):
        u = HandshakedBuilderSimple()
        self.prepareUnit(u)

        u.a._ag.data.extend([1, 2, 3, 4])

        buff = StringIO()
        self.dumpHdlTestbench(200 * Time.ns, buff)
        s = buff.getvalue()
        self.assertEqual(s, HandshakedBuilderSimple_dump)
        self.assertValSequenceEqual(u.b._ag.data, [1, 2, 3, 4])

HandshakedBuilderSimple_dump = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY HandshakedBuilderSimple_tb IS

END HandshakedBuilderSimple_tb;
ARCHITECTURE rtl OF HandshakedBuilderSimple_tb IS
    SIGNAL a_data: STD_LOGIC_VECTOR(63 DOWNTO 0) := X"0000000000000000";
    SIGNAL a_rd: STD_LOGIC := '0';
    SIGNAL a_vld: STD_LOGIC := '0';
    SIGNAL b_data: STD_LOGIC_VECTOR(63 DOWNTO 0) := X"0000000000000000";
    SIGNAL b_rd: STD_LOGIC := '0';
    SIGNAL b_vld: STD_LOGIC := '0';
    SIGNAL clk: STD_LOGIC := '0';
    SIGNAL rst_n: STD_LOGIC := '0';
    COMPONENT HandshakedBuilderSimple IS
       GENERIC (a_DATA_WIDTH: INTEGER := 64;
            b_DATA_WIDTH: INTEGER := 64
       );
       PORT (a_data: IN STD_LOGIC_VECTOR(a_DATA_WIDTH - 1 DOWNTO 0);
            a_rd: OUT STD_LOGIC;
            a_vld: IN STD_LOGIC;
            b_data: OUT STD_LOGIC_VECTOR(b_DATA_WIDTH - 1 DOWNTO 0);
            b_rd: IN STD_LOGIC;
            b_vld: OUT STD_LOGIC;
            clk: IN STD_LOGIC;
            rst_n: IN STD_LOGIC
       );
    END COMPONENT;

BEGIN
    HandshakedBuilderSimple_inst: COMPONENT HandshakedBuilderSimple
        GENERIC MAP (a_DATA_WIDTH => 64,
            b_DATA_WIDTH => 64
        )
        PORT MAP (a_data => a_data,
            a_rd => a_rd,
            a_vld => a_vld,
            b_data => b_data,
            b_rd => b_rd,
            b_vld => b_vld,
            clk => clk,
            rst_n => rst_n
        );

    a_data_driver: PROCESS --()
    BEGIN
        wait for 5 ns;
        a_data <= X"0000000000000001";
        wait for 20 ns;
        a_data <= X"0000000000000002";
        wait for 10 ns;
        a_data <= X"0000000000000003";
        wait for 10 ns;
        a_data <= X"0000000000000004";
        wait for 10 ns;
        a_data <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
        wait;
    END PROCESS;

    a_vld_driver: PROCESS --()
    BEGIN
        wait for 5 ns;
        a_vld <= '0';
        wait for 10 ns;
        a_vld <= '1';
        wait for 40 ns;
        a_vld <= '0';
        wait;
    END PROCESS;

    b_rd_driver: PROCESS --()
    BEGIN
        wait for 5 ns;
        b_rd <= '0';
        wait for 10 ns;
        b_rd <= '1';
        wait;
    END PROCESS;

    clk_driver: PROCESS --()
    BEGIN
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait;
    END PROCESS;

    rst_n_driver: PROCESS --()
    BEGIN
        rst_n <= '0';
        wait for 6 ns;
        rst_n <= '1';
        wait;
    END PROCESS;

END ARCHITECTURE rtl;"""

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FrameTemplateTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(DumpTestbenchTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)