LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY VhdlVectorAutoCastExample IS
    PORT(
        a : IN STD_LOGIC;
        b : OUT STD_LOGIC;
        c : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
        d : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        e : OUT STD_LOGIC;
        f : IN STD_LOGIC;
        g : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        i : OUT STD_LOGIC;
        j : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF VhdlVectorAutoCastExample IS
BEGIN
    b <= a;
    c(0) <= a;
    e <= d(0);
    assig_process_i: PROCESS(f, g)
        VARIABLE tmp_std_logic2vector_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
        VARIABLE tmpTypeConv_1 : UNSIGNED(0 DOWNTO 0);
        VARIABLE tmpTypeConv_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmp_std_logic2vector_0(0) := f;
        tmpTypeConv_1 := UNSIGNED(tmp_std_logic2vector_0) + UNSIGNED(g);
        tmpTypeConv_0 := STD_LOGIC_VECTOR(tmpTypeConv_1);
        i <= tmpTypeConv_0(0);
    END PROCESS;
    assig_process_j: PROCESS(f, g)
        VARIABLE tmp_std_logic2vector_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
        VARIABLE tmpTypeConv_1 : UNSIGNED(0 DOWNTO 0);
        VARIABLE tmpTypeConv_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmp_std_logic2vector_0(0) := f;
        tmpTypeConv_1 := UNSIGNED(g) + UNSIGNED(tmp_std_logic2vector_0);
        tmpTypeConv_0 := STD_LOGIC_VECTOR(tmpTypeConv_1);
        j <= tmpTypeConv_0(0);
    END PROCESS;
END ARCHITECTURE;
