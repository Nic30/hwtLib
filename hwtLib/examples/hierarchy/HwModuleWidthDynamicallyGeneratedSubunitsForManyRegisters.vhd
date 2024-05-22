LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    An unit which will extract selected circuit from parent on instantiation.
--    
ENTITY ExtractedHwModule IS
    PORT(
        clk : IN STD_LOGIC;
        i0 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        i1 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        r0_0 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        r0_1 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        sig_0 : IN BOOLEAN
    );
END ENTITY;

ARCHITECTURE rtl OF ExtractedHwModule IS
    SIGNAL r0_0_0 : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL r0_0_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL r0_1_0 : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL r0_1_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    r0_0 <= r0_0_0;
    r0_0_next <= i0;
    assig_process_r0_1: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF sig_0 THEN
                r0_1_0 <= X"00";
                r0_0_0 <= X"00";
            ELSE
                r0_1_0 <= r0_1_next;
                r0_0_0 <= r0_0_next;
            END IF;
        END IF;
    END PROCESS;
    r0_1 <= r0_1_0;
    r0_1_next <= i1;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    An unit which will extract selected circuit from parent on instantiation.
--    
ENTITY ExtractedHwModule_0 IS
    PORT(
        clk : IN STD_LOGIC;
        r1_0 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        r1_1 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        sig_0 : IN BOOLEAN;
        sig_uForR0_r0_0 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        sig_uForR0_r0_1 : IN STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ExtractedHwModule_0 IS
    SIGNAL r1_0_0 : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL r1_0_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL r1_1_0 : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL r1_1_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    r1_0 <= r1_0_0;
    r1_0_next <= sig_uForR0_r0_0;
    assig_process_r1_1: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF sig_0 THEN
                r1_1_0 <= X"00";
                r1_0_0 <= X"00";
            ELSE
                r1_1_0 <= r1_1_next;
                r1_0_0 <= r1_0_next;
            END IF;
        END IF;
    END PROCESS;
    r1_1 <= r1_1_0;
    r1_1_next <= sig_uForR0_r0_1;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters IS
    PORT(
        clk : IN STD_LOGIC;
        i0 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        i1 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        o : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        rst_n : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters IS
    --
    --    An unit which will extract selected circuit from parent on instantiation.
    --    
    COMPONENT ExtractedHwModule IS
        PORT(
            clk : IN STD_LOGIC;
            i0 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            i1 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            r0_0 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
            r0_1 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
            sig_0 : IN BOOLEAN
        );
    END COMPONENT;
    --
    --    An unit which will extract selected circuit from parent on instantiation.
    --    
    COMPONENT ExtractedHwModule_0 IS
        PORT(
            clk : IN STD_LOGIC;
            r1_0 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
            r1_1 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
            sig_0 : IN BOOLEAN;
            sig_uForR0_r0_0 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            sig_uForR0_r0_1 : IN STD_LOGIC_VECTOR(7 DOWNTO 0)
        );
    END COMPONENT;
    SIGNAL sig_uForR0_clk : STD_LOGIC;
    SIGNAL sig_uForR0_i0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR0_i1 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR0_r0_0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR0_r0_1 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR0_sig_0 : BOOLEAN;
    SIGNAL sig_uForR1_clk : STD_LOGIC;
    SIGNAL sig_uForR1_r1_0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR1_r1_1 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR1_sig_0 : BOOLEAN;
    SIGNAL sig_uForR1_sig_uForR0_r0_0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR1_sig_uForR0_r0_1 : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    uForR0_inst: ExtractedHwModule PORT MAP(
        clk => sig_uForR0_clk,
        i0 => sig_uForR0_i0,
        i1 => sig_uForR0_i1,
        r0_0 => sig_uForR0_r0_0,
        r0_1 => sig_uForR0_r0_1,
        sig_0 => sig_uForR0_sig_0
    );
    uForR1_inst: ExtractedHwModule_0 PORT MAP(
        clk => sig_uForR1_clk,
        r1_0 => sig_uForR1_r1_0,
        r1_1 => sig_uForR1_r1_1,
        sig_0 => sig_uForR1_sig_0,
        sig_uForR0_r0_0 => sig_uForR1_sig_uForR0_r0_0,
        sig_uForR0_r0_1 => sig_uForR1_sig_uForR0_r0_1
    );
    assig_process_o: PROCESS(sig_uForR1_r1_0, sig_uForR1_r1_1)
        VARIABLE tmpCastExpr_0 : UNSIGNED(7 DOWNTO 0);
    BEGIN
        tmpCastExpr_0 := UNSIGNED(sig_uForR1_r1_0) + UNSIGNED(sig_uForR1_r1_1);
        o <= STD_LOGIC_VECTOR(tmpCastExpr_0);
    END PROCESS;
    sig_uForR0_clk <= clk;
    sig_uForR0_i0 <= i0;
    sig_uForR0_i1 <= i1;
    sig_uForR0_sig_0 <= rst_n = '0';
    sig_uForR1_clk <= clk;
    sig_uForR1_sig_0 <= rst_n = '0';
    sig_uForR1_sig_uForR0_r0_0 <= sig_uForR0_r0_0;
    sig_uForR1_sig_uForR0_r0_1 <= sig_uForR0_r0_1;
END ARCHITECTURE;
