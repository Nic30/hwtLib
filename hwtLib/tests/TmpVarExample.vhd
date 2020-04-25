LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY TmpVarExample IS
    PORT(
        a : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(31 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF TmpVarExample IS
BEGIN
    assig_process_b: PROCESS(a)
        VARIABLE tmpTypeConv : UNSIGNED(3 DOWNTO 0);
        VARIABLE tmpTypeConv_0 : UNSIGNED(7 DOWNTO 0);
        VARIABLE tmpTypeConv_1 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    BEGIN
        tmpTypeConv := tmpTypeConv_0(3 DOWNTO 0);
        tmpTypeConv_0 := UNSIGNED(tmpTypeConv_1) + UNSIGNED'(X"04");
        tmpTypeConv_1 := a(7 DOWNTO 0);
        b <= X"0000000" & STD_LOGIC_VECTOR(tmpTypeConv);
    END PROCESS;
END ARCHITECTURE;
