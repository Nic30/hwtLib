--
--    .. hwt-schematic::
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleIfStatementMergable IS
    PORT (a: IN STD_LOGIC;
        b: IN STD_LOGIC;
        c: OUT STD_LOGIC;
        d: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleIfStatementMergable IS
BEGIN
    assig_process_d: PROCESS (a, b)
    BEGIN
        IF a = '1' THEN
            d <= b;
            c <= b;
        ELSE
            d <= '0';
            c <= '0';
        END IF;
    END PROCESS;

END ARCHITECTURE;
