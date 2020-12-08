LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY SimpleIfStatementMergable1 IS
    PORT(
        a : IN STD_LOGIC;
        b : IN STD_LOGIC;
        c : OUT STD_LOGIC;
        d : OUT STD_LOGIC;
        e : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleIfStatementMergable1 IS
BEGIN
    assig_process_c: PROCESS(a, b, e)
    BEGIN
        IF e = '1' THEN
            IF a = '1' THEN
                d <= b;
                c <= b;
            END IF;
        END IF;
    END PROCESS;
END ARCHITECTURE;
