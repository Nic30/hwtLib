LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ExampleHBitsMulS1a IS
    PORT(
        a : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        b : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        res : OUT STD_LOGIC_VECTOR(15 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ExampleHBitsMulS1a IS
BEGIN
    assig_process_res: PROCESS(a, b)
        VARIABLE tmpCastExpr_0 : UNSIGNED(15 DOWNTO 0);
    BEGIN
        tmpCastExpr_0 := SIGNED(a) * SIGNED(b);
        res <= STD_LOGIC_VECTOR(tmpCastExpr_0);
    END PROCESS;
END ARCHITECTURE;
