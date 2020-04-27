LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY TernaryInConcatExample IS
    PORT(
        a : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        b : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        c : OUT STD_LOGIC_VECTOR(31 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF TernaryInConcatExample IS
BEGIN
    assig_process_c: PROCESS(a, b)
        VARIABLE tmpBool2std_logic_0 : STD_LOGIC;
        VARIABLE tmpBool2std_logic_1 : STD_LOGIC;
        VARIABLE tmpBool2std_logic_2 : STD_LOGIC;
        VARIABLE tmpBool2std_logic_3 : STD_LOGIC;
        VARIABLE tmpBool2std_logic_4 : STD_LOGIC;
        VARIABLE tmpBool2std_logic_5 : STD_LOGIC;
    BEGIN
        IF a > b THEN
            tmpBool2std_logic_0 := '1';
        ELSE
            tmpBool2std_logic_0 := '0';
        END IF;
        IF a >= b THEN
            tmpBool2std_logic_1 := '1';
        ELSE
            tmpBool2std_logic_1 := '0';
        END IF;
        IF a = b THEN
            tmpBool2std_logic_2 := '1';
        ELSE
            tmpBool2std_logic_2 := '0';
        END IF;
        IF a <= b THEN
            tmpBool2std_logic_3 := '1';
        ELSE
            tmpBool2std_logic_3 := '0';
        END IF;
        IF a < b THEN
            tmpBool2std_logic_4 := '1';
        ELSE
            tmpBool2std_logic_4 := '0';
        END IF;
        IF a /= b THEN
            tmpBool2std_logic_5 := '1';
        ELSE
            tmpBool2std_logic_5 := '0';
        END IF;
        c <= X"F" & tmpBool2std_logic_5 & tmpBool2std_logic_4 & tmpBool2std_logic_3 & tmpBool2std_logic_2 & tmpBool2std_logic_1 & tmpBool2std_logic_0 & "0000000000000000000000";
    END PROCESS;
END ARCHITECTURE;
