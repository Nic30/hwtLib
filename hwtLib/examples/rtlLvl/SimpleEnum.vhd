LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleEnum IS
    PORT(
        clk : IN STD_LOGIC;
        rst : IN STD_LOGIC;
        s_in0 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_in1 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out : OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleEnum IS
    TYPE fsmT IS (send0, send1);
    SIGNAL fsmSt : fsmt := send0;
    SIGNAL fsmSt_next : fsmt;
BEGIN
    assig_process_fsmSt: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                fsmSt <= send0;
            ELSE
                fsmSt <= fsmSt_next;
            END IF;
        END IF;
    END PROCESS;
    assig_process_fsmSt_next: PROCESS(fsmSt, s_in0, s_in1)
    BEGIN
        IF fsmSt = send0 THEN
            s_out <= s_in0;
            fsmSt_next <= send1;
        ELSE
            s_out <= s_in1;
            fsmSt_next <= send0;
        END IF;
    END PROCESS;
END ARCHITECTURE;
