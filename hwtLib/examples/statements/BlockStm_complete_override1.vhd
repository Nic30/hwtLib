LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY BlockStm_complete_override1 IS
    PORT(
        a : IN STD_LOGIC;
        b : IN STD_LOGIC;
        c : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF BlockStm_complete_override1 IS
BEGIN
    assig_process_c: PROCESS(a, b)
    BEGIN
        c <= a;
        IF b = '1' THEN
            c <= '0';
        END IF;
    END PROCESS;
END ARCHITECTURE;
