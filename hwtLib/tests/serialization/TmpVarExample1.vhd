LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY TmpVarExample1 IS
    PORT(
        a : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(31 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF TmpVarExample1 IS
BEGIN
    assig_process_b: PROCESS(a)
        VARIABLE tmpTypeConv_0 : BOOLEAN;
        VARIABLE tmpTypeConv_1 : BOOLEAN;
    BEGIN
        tmpTypeConv_0 := a(15 DOWNTO 0) = X"0001";
        tmpTypeConv_1 := a(31 DOWNTO 16) = X"0001";
        IF tmpTypeConv_0 AND tmpTypeConv_1 THEN
            b <= X"00000000";
        ELSE
            b <= X"00000001";
        END IF;
    END PROCESS;
END ARCHITECTURE;
