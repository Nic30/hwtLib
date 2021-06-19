LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY TmpVarSignCast IS
    PORT(
        a : IN STD_LOGIC;
        b : IN UNSIGNED(0 DOWNTO 0);
        c : OUT UNSIGNED(0 DOWNTO 0);
        d : OUT UNSIGNED(0 DOWNTO 0);
        e : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        i : IN STD_LOGIC;
        o : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF TmpVarSignCast IS
BEGIN
    assig_process_c: PROCESS(a, b)
        VARIABLE tmp_std_logic2vector_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmp_std_logic2vector_0(0) := a;
        c <= UNSIGNED(tmp_std_logic2vector_0) + b;
    END PROCESS;
    assig_process_d: PROCESS(a, b)
        VARIABLE tmp_std_logic2vector_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmp_std_logic2vector_0(0) := a;
        d <= b + UNSIGNED(tmp_std_logic2vector_0);
    END PROCESS;
    assig_process_o: PROCESS(e, i)
        VARIABLE tmpTypeConv_0 : STD_LOGIC_VECTOR(0 DOWNTO 0);
    BEGIN
        tmpTypeConv_0(0) := i;
        o <= e(TO_INTEGER(UNSIGNED(tmpTypeConv_0)));
    END PROCESS;
END ARCHITECTURE;
