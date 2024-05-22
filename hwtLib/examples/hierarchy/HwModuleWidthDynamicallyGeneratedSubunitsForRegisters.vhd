LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    An unit which will extract selected circuit from parent on instantiation.
--    
ENTITY ExtractedHwModule IS
    PORT(
        clk : IN STD_LOGIC;
        i : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        r0 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        sig_0 : IN BOOLEAN
    );
END ENTITY;

ARCHITECTURE rtl OF ExtractedHwModule IS
    SIGNAL r0_0 : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL r0_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    assig_process_r0: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF sig_0 THEN
                r0_0 <= X"00";
            ELSE
                r0_0 <= r0_next;
            END IF;
        END IF;
    END PROCESS;
    r0 <= r0_0;
    r0_next <= i;
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
        r1 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        sig_0 : IN BOOLEAN;
        sig_uForR0_r0 : IN STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ExtractedHwModule_0 IS
    SIGNAL r1_0 : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL r1_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    assig_process_r1: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF sig_0 THEN
                r1_0 <= X"00";
            ELSE
                r1_0 <= r1_next;
            END IF;
        END IF;
    END PROCESS;
    r1 <= r1_0;
    r1_next <= sig_uForR0_r0;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY HwModuleWidthDynamicallyGeneratedSubunitsForRegisters IS
    PORT(
        clk : IN STD_LOGIC;
        i : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        o : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        rst_n : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF HwModuleWidthDynamicallyGeneratedSubunitsForRegisters IS
    --
    --    An unit which will extract selected circuit from parent on instantiation.
    --    
    COMPONENT ExtractedHwModule IS
        PORT(
            clk : IN STD_LOGIC;
            i : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            r0 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
            sig_0 : IN BOOLEAN
        );
    END COMPONENT;
    --
    --    An unit which will extract selected circuit from parent on instantiation.
    --    
    COMPONENT ExtractedHwModule_0 IS
        PORT(
            clk : IN STD_LOGIC;
            r1 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
            sig_0 : IN BOOLEAN;
            sig_uForR0_r0 : IN STD_LOGIC_VECTOR(7 DOWNTO 0)
        );
    END COMPONENT;
    SIGNAL sig_uForR0_clk : STD_LOGIC;
    SIGNAL sig_uForR0_i : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR0_r0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR0_sig_0 : BOOLEAN;
    SIGNAL sig_uForR1_clk : STD_LOGIC;
    SIGNAL sig_uForR1_r1 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_uForR1_sig_0 : BOOLEAN;
    SIGNAL sig_uForR1_sig_uForR0_r0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    uForR0_inst: ExtractedHwModule PORT MAP(
        clk => sig_uForR0_clk,
        i => sig_uForR0_i,
        r0 => sig_uForR0_r0,
        sig_0 => sig_uForR0_sig_0
    );
    uForR1_inst: ExtractedHwModule_0 PORT MAP(
        clk => sig_uForR1_clk,
        r1 => sig_uForR1_r1,
        sig_0 => sig_uForR1_sig_0,
        sig_uForR0_r0 => sig_uForR1_sig_uForR0_r0
    );
    o <= sig_uForR1_r1;
    sig_uForR0_clk <= clk;
    sig_uForR0_i <= i;
    sig_uForR0_sig_0 <= rst_n = '0';
    sig_uForR1_clk <= clk;
    sig_uForR1_sig_0 <= rst_n = '0';
    sig_uForR1_sig_uForR0_r0 <= sig_uForR0_r0;
END ARCHITECTURE;
