LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY Counter IS
    PORT(
        clk : IN STD_LOGIC;
        en : IN STD_LOGIC;
        rst : IN STD_LOGIC;
        s_out : OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF Counter IS
    SIGNAL cnt : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL cnt_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    assig_process_cnt: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                cnt <= X"00";
            ELSE
                cnt <= cnt_next;
            END IF;
        END IF;
    END PROCESS;
    assig_process_cnt_next: PROCESS(cnt, en)
        VARIABLE tmpTypeConv_0 : UNSIGNED(7 DOWNTO 0);
    BEGIN
        tmpTypeConv_0 := UNSIGNED(cnt) + UNSIGNED'(X"01");
        IF en = '1' THEN
            cnt_next <= STD_LOGIC_VECTOR(tmpTypeConv_0);
        ELSE
            cnt_next <= cnt;
        END IF;
    END PROCESS;
    s_out <= cnt;
END ARCHITECTURE;
