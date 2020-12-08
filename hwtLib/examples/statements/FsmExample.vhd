LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY FsmExample IS
    PORT(
        a : IN STD_LOGIC;
        b : IN STD_LOGIC;
        clk : IN STD_LOGIC;
        dout : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
        rst_n : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF FsmExample IS
    TYPE st_t IS (a_0, b_0, aAndB);
    SIGNAL st : st_t := a_0;
    SIGNAL st_next : st_t;
BEGIN
    assig_process_dout: PROCESS(st)
    BEGIN
        CASE st IS
            WHEN a_0 =>
                dout <= "001";
            WHEN b_0 =>
                dout <= "010";
            WHEN OTHERS =>
                dout <= "011";
        END CASE;
    END PROCESS;
    assig_process_st: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst_n = '0' THEN
                st <= a_0;
            ELSE
                st <= st_next;
            END IF;
        END IF;
    END PROCESS;
    assig_process_st_next: PROCESS(a, b, st)
    BEGIN
        CASE st IS
            WHEN a_0 =>
                IF (a AND b) = '1' THEN
                    st_next <= aandb;
                ELSIF b = '1' THEN
                    st_next <= b_0;
                ELSE
                    st_next <= st;
                END IF;
            WHEN b_0 =>
                IF (a AND b) = '1' THEN
                    st_next <= aandb;
                ELSIF a = '1' THEN
                    st_next <= a_0;
                ELSE
                    st_next <= st;
                END IF;
            WHEN OTHERS =>
                IF (a AND NOT b) = '1' THEN
                    st_next <= a_0;
                ELSIF (NOT a AND b) = '1' THEN
                    st_next <= b_0;
                ELSE
                    st_next <= st;
                END IF;
        END CASE;
    END PROCESS;
END ARCHITECTURE;
