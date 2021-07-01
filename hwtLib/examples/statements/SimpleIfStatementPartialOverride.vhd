LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY SimpleIfStatementPartialOverride IS
    PORT(
        a : IN STD_LOGIC;
        b : IN STD_LOGIC;
        c : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleIfStatementPartialOverride IS
BEGIN
    assig_process_c: PROCESS(a, b)
    BEGIN
        IF b = '1' THEN
            c <= '1';
            IF a = '1' THEN
                c <= b;
            END IF;
        END IF;
    END PROCESS;
END ARCHITECTURE;
