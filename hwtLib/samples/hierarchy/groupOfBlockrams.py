#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect
from hwt.interfaces.std import Signal, Clk, VectSignal
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.mem.ram import Ram_dp


class GroupOfBlockrams(Unit):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        with self._paramsShared():
            def extData():
                return VectSignal(self.DATA_WIDTH)

            self.clk = Clk()
            self.en = Signal()
            self.we = Signal()

            self.addr = VectSignal(self.ADDR_WIDTH)
            self.in_w_a = extData()
            self.in_w_b = extData()
            self.in_r_a = extData()
            self.in_r_b = extData()

            self.out_w_a = extData()
            self.out_w_b = extData()
            self.out_r_a = extData()
            self.out_r_b = extData()

            with self._paramsShared():
                self.bramR = Ram_dp()
                self.bramW = Ram_dp()

    def _impl(self):
        s = self
        bramR = s.bramR
        bramW = s.bramW

        all_bram_ports = [bramR.a, bramR.b, bramW.a, bramW.b]

        connect(s.clk, *map(lambda i: i.clk, all_bram_ports))
        connect(s.en, *map(lambda i: i.en, all_bram_ports))
        connect(s.we, *map(lambda i: i.we, all_bram_ports))
        connect(s.addr, *map(lambda i: i.addr, all_bram_ports))

        bramW.a.din ** s.in_w_a
        bramW.b.din ** s.in_w_b
        bramR.a.din ** s.in_r_a
        bramR.b.din ** s.in_r_b
        s.out_w_a ** bramW.a.dout
        s.out_w_b ** bramW.b.dout
        s.out_r_a ** bramR.a.dout
        s.out_r_b ** bramR.b.dout

groupOfBlockrams_as_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY bramR IS
    GENERIC (ADDR_WIDTH: INTEGER := 8;
        DATA_WIDTH: INTEGER := 64
    );
    PORT (a_addr: IN STD_LOGIC_VECTOR(ADDR_WIDTH - 1 DOWNTO 0);
        a_clk: IN STD_LOGIC;
        a_din: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        a_dout: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        a_en: IN STD_LOGIC;
        a_we: IN STD_LOGIC;
        b_addr: IN STD_LOGIC_VECTOR(ADDR_WIDTH - 1 DOWNTO 0);
        b_clk: IN STD_LOGIC;
        b_din: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        b_dout: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        b_en: IN STD_LOGIC;
        b_we: IN STD_LOGIC
    );
END bramR;

ARCHITECTURE rtl OF bramR IS
    TYPE arrT_0 IS ARRAY ((2 ** ADDR_WIDTH - 1) DOWNTO 0) OF STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
    SIGNAL ram_memory: arrT_0;
BEGIN
    assig_process_a_dout: PROCESS (a_clk)
    BEGIN
        IF (RISING_EDGE(a_clk)) AND (a_en = '1') THEN
            a_dout <= ram_memory(TO_INTEGER(UNSIGNED(a_addr)));
        END IF;
    END PROCESS;

    assig_process_b_dout: PROCESS (b_clk)
    BEGIN
        IF (RISING_EDGE(b_clk)) AND (b_en = '1') THEN
            b_dout <= ram_memory(TO_INTEGER(UNSIGNED(b_addr)));
        END IF;
    END PROCESS;

    assig_process_ram_memory: PROCESS (a_clk)
    BEGIN
        IF (RISING_EDGE(a_clk)) AND (a_en = '1') AND a_we = '1' THEN
            ram_memory(TO_INTEGER(UNSIGNED(a_addr))) <= a_din;
        END IF;
    END PROCESS;

    assig_process_ram_memory_0: PROCESS (b_clk)
    BEGIN
        IF (RISING_EDGE(b_clk)) AND (b_en = '1') AND b_we = '1' THEN
            ram_memory(TO_INTEGER(UNSIGNED(b_addr))) <= b_din;
        END IF;
    END PROCESS;

END ARCHITECTURE rtl;
--Object of class Entity, "bramR" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY GroupOfBlockrams IS
    GENERIC (ADDR_WIDTH: INTEGER := 8;
        DATA_WIDTH: INTEGER := 64
    );
    PORT (addr: IN STD_LOGIC_VECTOR(ADDR_WIDTH - 1 DOWNTO 0);
        clk: IN STD_LOGIC;
        en: IN STD_LOGIC;
        in_r_a: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        in_r_b: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        in_w_a: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        in_w_b: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        out_r_a: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        out_r_b: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        out_w_a: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        out_w_b: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        we: IN STD_LOGIC
    );
END GroupOfBlockrams;

ARCHITECTURE rtl OF GroupOfBlockrams IS
    SIGNAL sig_bramR_a_addr: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramR_a_clk: STD_LOGIC;
    SIGNAL sig_bramR_a_din: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_a_dout: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_a_en: STD_LOGIC;
    SIGNAL sig_bramR_a_we: STD_LOGIC;
    SIGNAL sig_bramR_b_addr: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramR_b_clk: STD_LOGIC;
    SIGNAL sig_bramR_b_din: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_b_dout: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_b_en: STD_LOGIC;
    SIGNAL sig_bramR_b_we: STD_LOGIC;
    SIGNAL sig_bramW_a_addr: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramW_a_clk: STD_LOGIC;
    SIGNAL sig_bramW_a_din: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_a_dout: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_a_en: STD_LOGIC;
    SIGNAL sig_bramW_a_we: STD_LOGIC;
    SIGNAL sig_bramW_b_addr: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramW_b_clk: STD_LOGIC;
    SIGNAL sig_bramW_b_din: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_b_dout: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_b_en: STD_LOGIC;
    SIGNAL sig_bramW_b_we: STD_LOGIC;
    COMPONENT bramR IS
       GENERIC (ADDR_WIDTH: INTEGER := 8;
            DATA_WIDTH: INTEGER := 64
       );
       PORT (a_addr: IN STD_LOGIC_VECTOR(ADDR_WIDTH - 1 DOWNTO 0);
            a_clk: IN STD_LOGIC;
            a_din: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
            a_dout: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
            a_en: IN STD_LOGIC;
            a_we: IN STD_LOGIC;
            b_addr: IN STD_LOGIC_VECTOR(ADDR_WIDTH - 1 DOWNTO 0);
            b_clk: IN STD_LOGIC;
            b_din: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
            b_dout: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
            b_en: IN STD_LOGIC;
            b_we: IN STD_LOGIC
       );
    END COMPONENT;

BEGIN
    bramR_inst: COMPONENT bramR
        GENERIC MAP (ADDR_WIDTH => 8,
            DATA_WIDTH => 64
        )
        PORT MAP (a_addr => sig_bramR_a_addr,
            a_clk => sig_bramR_a_clk,
            a_din => sig_bramR_a_din,
            a_dout => sig_bramR_a_dout,
            a_en => sig_bramR_a_en,
            a_we => sig_bramR_a_we,
            b_addr => sig_bramR_b_addr,
            b_clk => sig_bramR_b_clk,
            b_din => sig_bramR_b_din,
            b_dout => sig_bramR_b_dout,
            b_en => sig_bramR_b_en,
            b_we => sig_bramR_b_we
        );

    bramW_inst: COMPONENT bramR
        GENERIC MAP (ADDR_WIDTH => 8,
            DATA_WIDTH => 64
        )
        PORT MAP (a_addr => sig_bramW_a_addr,
            a_clk => sig_bramW_a_clk,
            a_din => sig_bramW_a_din,
            a_dout => sig_bramW_a_dout,
            a_en => sig_bramW_a_en,
            a_we => sig_bramW_a_we,
            b_addr => sig_bramW_b_addr,
            b_clk => sig_bramW_b_clk,
            b_din => sig_bramW_b_din,
            b_dout => sig_bramW_b_dout,
            b_en => sig_bramW_b_en,
            b_we => sig_bramW_b_we
        );

    out_r_a <= sig_bramR_a_dout;
    out_r_b <= sig_bramR_b_dout;
    out_w_a <= sig_bramW_a_dout;
    out_w_b <= sig_bramW_b_dout;
    sig_bramR_a_addr <= addr;
    sig_bramR_a_clk <= clk;
    sig_bramR_a_din <= in_r_a;
    sig_bramR_a_en <= en;
    sig_bramR_a_we <= we;
    sig_bramR_b_addr <= addr;
    sig_bramR_b_clk <= clk;
    sig_bramR_b_din <= in_r_b;
    sig_bramR_b_en <= en;
    sig_bramR_b_we <= we;
    sig_bramW_a_addr <= addr;
    sig_bramW_a_clk <= clk;
    sig_bramW_a_din <= in_w_a;
    sig_bramW_a_en <= en;
    sig_bramW_a_we <= we;
    sig_bramW_b_addr <= addr;
    sig_bramW_b_clk <= clk;
    sig_bramW_b_din <= in_w_b;
    sig_bramW_b_en <= en;
    sig_bramW_b_we <= we;
END ARCHITECTURE rtl;"""

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(GroupOfBlockrams()))
