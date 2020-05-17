LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleWhile IS
    PORT(
        clk : IN STD_LOGIC;
        en : IN STD_LOGIC;
        rst : IN STD_LOGIC;
        s_out : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        start : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleWhile IS
    CONSTANT boundary : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"08";
    SIGNAL counter : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL counter_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    assig_process_counter: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                counter <= X"00";
            ELSE
                counter <= counter_next;
            END IF;
        END IF;
    END PROCESS;
    assig_process_counter_next: PROCESS(counter, en, start)
        VARIABLE tmpTypeConv_0 : UNSIGNED(7 DOWNTO 0);
    BEGIN
        tmpTypeConv_0 := UNSIGNED(counter) - UNSIGNED'(X"01");
        IF start = '1' THEN
            counter_next <= boundary;
        ELSIF en = '1' THEN
            counter_next <= STD_LOGIC_VECTOR(tmpTypeConv_0);
        ELSE
            counter_next <= counter;
        END IF;
    END PROCESS;
    s_out <= counter;
END ARCHITECTURE;
