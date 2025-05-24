LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY TmpVarZExtBool IS
    PORT(
        a : IN UNSIGNED(7 DOWNTO 0);
        b : IN UNSIGNED(7 DOWNTO 0);
        o0 : OUT STD_LOGIC;
        o0_2b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        o0_2b_s : OUT SIGNED(1 DOWNTO 0);
        o0_2b_u : OUT UNSIGNED(1 DOWNTO 0);
        o0_3b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
        o0_3b_s : OUT SIGNED(2 DOWNTO 0);
        o0_3b_u : OUT UNSIGNED(2 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF TmpVarZExtBool IS
BEGIN
    o0 <= '1' WHEN (a < b) ELSE '0';
    assig_process_o0_2b: PROCESS(a, b)
        VARIABLE tmpBool2std_logic_0 : STD_LOGIC;
    BEGIN
        IF a < b THEN
            tmpBool2std_logic_0 := '1';
        ELSE
            tmpBool2std_logic_0 := '0';
        END IF;
        o0_2b <= (0 => tmpBool2std_logic_0, OTHERS => '0');
    END PROCESS;
    assig_process_o0_2b_s: PROCESS(a, b)
        VARIABLE tmpBool2std_logic_0 : STD_LOGIC;
        VARIABLE tmpCastExpr_0 : STD_LOGIC_VECTOR(1 DOWNTO 0);
    BEGIN
        IF a < b THEN
            tmpBool2std_logic_0 := '1';
        ELSE
            tmpBool2std_logic_0 := '0';
        END IF;
        tmpCastExpr_0 := (0 => tmpBool2std_logic_0, OTHERS => '0');
        o0_2b_s <= SIGNED(tmpCastExpr_0);
    END PROCESS;
    assig_process_o0_2b_u: PROCESS(a, b)
        VARIABLE tmpBool2std_logic_0 : STD_LOGIC;
        VARIABLE tmpCastExpr_0 : STD_LOGIC_VECTOR(1 DOWNTO 0);
    BEGIN
        IF a < b THEN
            tmpBool2std_logic_0 := '1';
        ELSE
            tmpBool2std_logic_0 := '0';
        END IF;
        tmpCastExpr_0 := (0 => tmpBool2std_logic_0, OTHERS => '0');
        o0_2b_u <= UNSIGNED(tmpCastExpr_0);
    END PROCESS;
    assig_process_o0_3b: PROCESS(a, b)
        VARIABLE tmpBool2std_logic_0 : STD_LOGIC;
    BEGIN
        IF a < b THEN
            tmpBool2std_logic_0 := '1';
        ELSE
            tmpBool2std_logic_0 := '0';
        END IF;
        o0_3b <= (0 => tmpBool2std_logic_0, OTHERS => '0');
    END PROCESS;
    assig_process_o0_3b_s: PROCESS(a, b)
        VARIABLE tmpBool2std_logic_0 : STD_LOGIC;
        VARIABLE tmpCastExpr_0 : STD_LOGIC_VECTOR(2 DOWNTO 0);
    BEGIN
        IF a < b THEN
            tmpBool2std_logic_0 := '1';
        ELSE
            tmpBool2std_logic_0 := '0';
        END IF;
        tmpCastExpr_0 := (0 => tmpBool2std_logic_0, OTHERS => '0');
        o0_3b_s <= SIGNED(tmpCastExpr_0);
    END PROCESS;
    assig_process_o0_3b_u: PROCESS(a, b)
        VARIABLE tmpBool2std_logic_0 : STD_LOGIC;
        VARIABLE tmpCastExpr_0 : STD_LOGIC_VECTOR(2 DOWNTO 0);
    BEGIN
        IF a < b THEN
            tmpBool2std_logic_0 := '1';
        ELSE
            tmpBool2std_logic_0 := '0';
        END IF;
        tmpCastExpr_0 := (0 => tmpBool2std_logic_0, OTHERS => '0');
        o0_3b_u <= UNSIGNED(tmpCastExpr_0);
    END PROCESS;
END ARCHITECTURE;
