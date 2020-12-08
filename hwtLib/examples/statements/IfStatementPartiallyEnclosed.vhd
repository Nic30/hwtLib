LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY IfStatementPartiallyEnclosed IS
    PORT(
        a : OUT STD_LOGIC;
        b : OUT STD_LOGIC;
        c : IN STD_LOGIC;
        clk : IN STD_LOGIC;
        d : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF IfStatementPartiallyEnclosed IS
    SIGNAL a_reg : STD_LOGIC;
    SIGNAL a_reg_next : STD_LOGIC;
    SIGNAL b_reg : STD_LOGIC;
    SIGNAL b_reg_next : STD_LOGIC;
BEGIN
    a <= a_reg;
    assig_process_a_reg_next: PROCESS(b_reg, c, d)
    BEGIN
        IF c = '1' THEN
            a_reg_next <= '1';
            b_reg_next <= '1';
        ELSIF d = '1' THEN
            a_reg_next <= '0';
            b_reg_next <= b_reg;
        ELSE
            a_reg_next <= '1';
            b_reg_next <= '1';
        END IF;
    END PROCESS;
    b <= b_reg;
    assig_process_b_reg: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            b_reg <= b_reg_next;
            a_reg <= a_reg_next;
        END IF;
    END PROCESS;
END ARCHITECTURE;
