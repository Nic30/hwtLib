LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY LeadingOne IS
    PORT(
        s_in : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_leadingOneCnt : OUT STD_LOGIC_VECTOR(3 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF LeadingOne IS
BEGIN
    assig_process_s_leadingOneCnt: PROCESS(s_in)
    BEGIN
        IF s_in(7) = '0' THEN
            s_leadingOneCnt <= X"0";
        ELSIF s_in(6) = '0' THEN
            s_leadingOneCnt <= X"1";
        ELSIF s_in(5) = '0' THEN
            s_leadingOneCnt <= X"2";
        ELSIF s_in(4) = '0' THEN
            s_leadingOneCnt <= X"3";
        ELSIF s_in(3) = '0' THEN
            s_leadingOneCnt <= X"4";
        ELSIF s_in(2) = '0' THEN
            s_leadingOneCnt <= X"5";
        ELSIF s_in(1) = '0' THEN
            s_leadingOneCnt <= X"6";
        ELSIF s_in(0) = '0' THEN
            s_leadingOneCnt <= X"7";
        ELSE
            s_leadingOneCnt <= X"8";
        END IF;
    END PROCESS;
END ARCHITECTURE;
