LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleRegister IS
    PORT(
        clk : IN STD_LOGIC;
        rst : IN STD_LOGIC;
        s_in : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out : OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleRegister IS
    SIGNAL val : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL val_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    s_out <= val;
    assig_process_val: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                val <= X"00";
            ELSE
                val <= val_next;
            END IF;
        END IF;
    END PROCESS;
    val_next <= s_in;
END ARCHITECTURE;
