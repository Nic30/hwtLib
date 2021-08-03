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
        VARIABLE tmpTernaryAutoCast_0 : STD_LOGIC;
    BEGIN
        tmpTernaryAutoCast_0 := b(0);
        d(0) <= a WHEN (c = '1') ELSE tmpTernaryAutoCast_0;
    END PROCESS;
    assig_process_e: PROCESS(a, b, c)
        VARIABLE tmpTernaryAutoCast_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmpTernaryAutoCast_0(0) := a;
        e <= b WHEN (c = '1') ELSE tmpTernaryAutoCast_0;
    END PROCESS;
    assig_process_f: PROCESS(a, b, c)
        VARIABLE tmpTernaryAutoCast_0 : STD_LOGIC;
    BEGIN
        tmpTernaryAutoCast_0 := b(0);
        f <= a WHEN (c = '1') ELSE tmpTernaryAutoCast_0;
    END PROCESS;
    assig_process_g: PROCESS(a, b, c)
        VARIABLE tmpTernaryAutoCast_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
        VARIABLE tmpTypeConv_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmpTernaryAutoCast_0(0) := a;
        tmpTypeConv_0 := b WHEN (c = '1') ELSE tmpTernaryAutoCast_0;
        g <= tmpTypeConv_0(0);
    END PROCESS;
END ARCHITECTURE;
