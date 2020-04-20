library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
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
        VARIABLE tmpTypeConv : STD_LOGIC_VECTOR(0 DOWNTO 0);
        VARIABLE tmpTypeConv_0 : UNSIGNED(0 DOWNTO 0);
        VARIABLE tmp_std_logic2vector : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmpTypeConv := STD_LOGIC_VECTOR(tmpTypeConv_0);
        tmpTypeConv_0 := UNSIGNED(tmp_std_logic2vector) + UNSIGNED(g);
        tmp_std_logic2vector(0) := f;
        i <= tmpTypeConv(0);
    END PROCESS;
    assig_process_j: PROCESS(f, g)
        VARIABLE tmpTypeConv_1 : STD_LOGIC_VECTOR(0 DOWNTO 0);
        VARIABLE tmpTypeConv_2 : UNSIGNED(0 DOWNTO 0);
        VARIABLE tmp_std_logic2vector_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmpTypeConv_1 := STD_LOGIC_VECTOR(tmpTypeConv_2);
        tmpTypeConv_2 := UNSIGNED(g) + UNSIGNED(tmp_std_logic2vector_0);
        tmp_std_logic2vector_0(0) := f;
        j <= tmpTypeConv_1(0);
    END PROCESS;
END ARCHITECTURE;


