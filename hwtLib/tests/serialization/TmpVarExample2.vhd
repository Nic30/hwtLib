LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY TmpVarExample2 IS
    PORT(
        a : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(31 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF TmpVarExample2 IS
BEGIN
    assig_process_b: PROCESS(a)
        VARIABLE tmpBool2std_logic_0 : STD_LOGIC;
        VARIABLE tmpBool2std_logic_1 : STD_LOGIC;
        VARIABLE tmpCastExpr_0 : STD_LOGIC_VECTOR(1 DOWNTO 0);
        VARIABLE tmpTypeConv_0 : UNSIGNED(1 DOWNTO 0);
    BEGIN
        IF a(31 DOWNTO 16) = X"0001" THEN
            tmpBool2std_logic_0 := '1';
        ELSE
            tmpBool2std_logic_0 := '0';
        END IF;
        IF a(15 DOWNTO 0) = X"0001" THEN
            tmpBool2std_logic_1 := '1';
        ELSE
            tmpBool2std_logic_1 := '0';
        END IF;
        tmpCastExpr_0 := tmpBool2std_logic_0 & tmpBool2std_logic_1;
        tmpTypeConv_0 := UNSIGNED(tmpCastExpr_0) + UNSIGNED'("01");
        IF tmpTypeConv_0(1) = '0' AND tmpTypeConv_0(0) = '0' THEN
            b <= X"00000000";
        ELSE
            b <= X"00000001";
        END IF;
    END PROCESS;
END ARCHITECTURE;
