LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY LeadingZero IS
    PORT(
        s_in : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_leadingZeroCnt : OUT STD_LOGIC_VECTOR(3 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF LeadingZero IS
BEGIN
    assig_process_s_leadingZeroCnt: PROCESS(s_in)
    BEGIN
        IF s_in(7) = '1' THEN
            s_leadingZeroCnt <= X"0";
        ELSIF s_in(6) = '1' THEN
            s_leadingZeroCnt <= X"1";
        ELSIF s_in(5) = '1' THEN
            s_leadingZeroCnt <= X"2";
        ELSIF s_in(4) = '1' THEN
            s_leadingZeroCnt <= X"3";
        ELSIF s_in(3) = '1' THEN
            s_leadingZeroCnt <= X"4";
        ELSIF s_in(2) = '1' THEN
            s_leadingZeroCnt <= X"5";
        ELSIF s_in(1) = '1' THEN
            s_leadingZeroCnt <= X"6";
        ELSIF s_in(0) = '1' THEN
            s_leadingZeroCnt <= X"7";
        ELSE
            s_leadingZeroCnt <= X"8";
        END IF;
    END PROCESS;
END ARCHITECTURE;
