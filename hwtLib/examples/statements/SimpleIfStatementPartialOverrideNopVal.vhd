LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY SimpleIfStatementPartialOverrideNopVal IS
    PORT(
        a : IN STD_LOGIC;
        b : IN STD_LOGIC;
        c : IN STD_LOGIC;
        clk : IN STD_LOGIC;
        e : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleIfStatementPartialOverrideNopVal IS
    SIGNAL d : STD_LOGIC;
    SIGNAL d_next : STD_LOGIC;
BEGIN
    assig_process_d: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            d <= d_next;
        END IF;
    END PROCESS;
    assig_process_d_next: PROCESS(a, b, c, d)
    BEGIN
        IF a = '1' THEN
            IF b = '1' THEN
                d_next <= '1';
            ELSE
                d_next <= d;
            END IF;
            IF c = '1' THEN
                d_next <= '0';
            END IF;
        ELSE
            d_next <= d;
        END IF;
    END PROCESS;
    e <= d;
END ARCHITECTURE;
