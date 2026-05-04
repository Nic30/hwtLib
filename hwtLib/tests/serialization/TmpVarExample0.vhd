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
        VARIABLE tmpCastExpr_2 : STD_LOGIC_VECTOR(7 DOWNTO 0);
        VARIABLE tmpCastExpr_1 : UNSIGNED(7 DOWNTO 0);
        VARIABLE tmpTruncLhs_0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
        VARIABLE tmpCastExpr_0 : STD_LOGIC_VECTOR(3 DOWNTO 0);
    BEGIN
        tmpCastExpr_2 := a(7 DOWNTO 0);
        tmpCastExpr_1 := UNSIGNED(tmpCastExpr_2) + UNSIGNED'(X"04");
        tmpTruncLhs_0 := STD_LOGIC_VECTOR(tmpCastExpr_1);
        tmpCastExpr_0 := tmpTruncLhs_0(3 DOWNTO 0);
        b <= STD_LOGIC_VECTOR(RESIZE(UNSIGNED(tmpCastExpr_0), 32));
    END PROCESS;
END ARCHITECTURE;
