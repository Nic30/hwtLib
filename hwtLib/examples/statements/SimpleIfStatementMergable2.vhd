LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY SimpleIfStatementMergable2 IS
    PORT(
        a : IN STD_LOGIC;
        b : IN STD_LOGIC;
        c : IN STD_LOGIC;
        d : OUT STD_LOGIC;
        e : OUT STD_LOGIC;
        f : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleIfStatementMergable2 IS
BEGIN
    assig_process_d: PROCESS(a, b, c)
    BEGIN
        IF a = '1' THEN
            d <= b;
            IF b = '1' THEN
                e <= c;
                f <= '0';
            END IF;
        ELSE
            d <= '0';
        END IF;
    END PROCESS;
END ARCHITECTURE;
