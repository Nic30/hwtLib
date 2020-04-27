LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ComplexConditions IS
    PORT(
        clk : IN STD_LOGIC;
        ctrlFifoLast : IN STD_LOGIC;
        ctrlFifoVld : IN STD_LOGIC;
        rst : IN STD_LOGIC;
        s_idle : OUT STD_LOGIC;
        sd0 : IN STD_LOGIC;
        sd1 : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF ComplexConditions IS
    TYPE t_state IS (idle, tsWait, ts0Wait, ts1Wait, lenExtr);
    SIGNAL st : t_state := idle;
    SIGNAL st_next : t_state;
BEGIN
    s_idle <= '1' WHEN (st = idle) ELSE '0';
    assig_process_st: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                st <= idle;
            ELSE
                st <= st_next;
            END IF;
        END IF;
    END PROCESS;
    assig_process_st_next: PROCESS(ctrlFifoLast, ctrlFifoVld, sd0, sd1, st)
    BEGIN
        CASE st IS
            WHEN idle =>
                IF (sd0 AND sd1) = '1' THEN
                    st_next <= lenextr;
                ELSIF sd0 = '1' THEN
                    st_next <= ts1wait;
                ELSIF sd1 = '1' THEN
                    st_next <= ts0wait;
                ELSIF ctrlFifoVld = '1' THEN
                    st_next <= tswait;
                ELSE
                    st_next <= st;
                END IF;
            WHEN tswait =>
                IF (sd0 AND sd1) = '1' THEN
                    st_next <= lenextr;
                ELSIF sd0 = '1' THEN
                    st_next <= ts1wait;
                ELSIF sd1 = '1' THEN
                    st_next <= ts0wait;
                ELSE
                    st_next <= st;
                END IF;
            WHEN ts0wait =>
                IF sd0 = '1' THEN
                    st_next <= lenextr;
                ELSE
                    st_next <= st;
                END IF;
            WHEN ts1wait =>
                IF sd1 = '1' THEN
                    st_next <= lenextr;
                ELSE
                    st_next <= st;
                END IF;
            WHEN OTHERS =>
                IF (ctrlFifoVld AND ctrlFifoLast) = '1' THEN
                    st_next <= idle;
                ELSE
                    st_next <= st;
                END IF;
        END CASE;
    END PROCESS;
END ARCHITECTURE;
