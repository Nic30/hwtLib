LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY TmpVarExampleTernary IS
    PORT(
        a : IN STD_LOGIC;
        b : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        c : IN STD_LOGIC;
        d : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
        e : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
        f : OUT STD_LOGIC;
        g : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF TmpVarExampleTernary IS
BEGIN
    assig_process_d: PROCESS(a, b, c)
        VARIABLE tmpTypeConv_0 : STD_LOGIC;
    BEGIN
        tmpTypeConv_0 := b(0);
        d(0) <= a WHEN (c = '1') ELSE tmpTypeConv_0;
    END PROCESS;
    assig_process_e: PROCESS(a, b, c)
        VARIABLE tmpTypeConv_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmpTypeConv_0(0) := a;
        e <= b WHEN (c = '1') ELSE tmpTypeConv_0;
    END PROCESS;
    assig_process_f: PROCESS(a, b, c)
        VARIABLE tmpTypeConv_0 : STD_LOGIC;
    BEGIN
        tmpTypeConv_0 := b(0);
        f <= a WHEN (c = '1') ELSE tmpTypeConv_0;
    END PROCESS;
    assig_process_g: PROCESS(a, b, c)
        VARIABLE tmpTypeConv_1 : STD_LOGIC_VECTOR(0 DOWNTO 0);
        VARIABLE tmpTypeConv_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmpTypeConv_1(0) := a;
        tmpTypeConv_0 := b WHEN (c = '1') ELSE tmpTypeConv_1;
        g <= tmpTypeConv_0(0);
    END PROCESS;
END ARCHITECTURE;
