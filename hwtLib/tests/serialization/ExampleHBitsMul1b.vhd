LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ExampleHBitsMul1b IS
    PORT(
        a : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        b : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        c : IN STD_LOGIC_VECTOR(15 DOWNTO 0);
        res : OUT STD_LOGIC_VECTOR(15 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ExampleHBitsMul1b IS
BEGIN
    assig_process_res: PROCESS(a, b, c)
        VARIABLE tmpCastExpr_0 : UNSIGNED(15 DOWNTO 0);
    BEGIN
        tmpCastExpr_0 := UNSIGNED(a) * UNSIGNED(b) + UNSIGNED(c);
        res <= STD_LOGIC_VECTOR(tmpCastExpr_0);
    END PROCESS;
END ARCHITECTURE;
