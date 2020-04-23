LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY LeadingZero IS
    PORT(
        s_in : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        s_indexOfFirstZero : OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF LeadingZero IS
BEGIN
    assig_process_s_indexOfFirstZero: PROCESS(s_in)
    BEGIN
        IF s_in(0) = '0' THEN
            s_indexOfFirstZero <= X"00";
        ELSIF s_in(1) = '0' THEN
            s_indexOfFirstZero <= X"01";
        ELSIF s_in(2) = '0' THEN
            s_indexOfFirstZero <= X"02";
        ELSIF s_in(3) = '0' THEN
            s_indexOfFirstZero <= X"03";
        ELSIF s_in(4) = '0' THEN
            s_indexOfFirstZero <= X"04";
        ELSIF s_in(5) = '0' THEN
            s_indexOfFirstZero <= X"05";
        ELSIF s_in(6) = '0' THEN
            s_indexOfFirstZero <= X"06";
        ELSE
            s_indexOfFirstZero <= X"07";
        END IF;
    END PROCESS;
END ARCHITECTURE;
