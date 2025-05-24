LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY TmpVarExample0 IS
    PORT(
        a : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(31 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF TmpVarExample0 IS
BEGIN
    assig_process_b: PROCESS(a)
        VARIABLE tmpCastExpr_1 : STD_LOGIC_VECTOR(7 DOWNTO 0);
        VARIABLE tmpTypeConv_0 : UNSIGNED(7 DOWNTO 0);
        VARIABLE tmpCastExpr_0 : UNSIGNED(31 DOWNTO 0);
    BEGIN
        tmpCastExpr_1 := a(7 DOWNTO 0);
        tmpTypeConv_0 := UNSIGNED(tmpCastExpr_1) + UNSIGNED'(X"04");
        tmpCastExpr_0 := RESIZE(RESIZE(tmpTypeConv_0, 4), 32);
        b <= STD_LOGIC_VECTOR(tmpCastExpr_0);
    END PROCESS;
END ARCHITECTURE;
