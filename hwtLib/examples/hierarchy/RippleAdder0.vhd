LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY FullAdder IS
    PORT(
        a : IN STD_LOGIC;
        b : IN STD_LOGIC;
        ci : IN STD_LOGIC;
        co : OUT STD_LOGIC;
        s : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF FullAdder IS
BEGIN
    co <= (a AND b) OR (a AND ci) OR (b AND ci);
    s <= a XOR b XOR ci;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY RippleAdder0 IS
    GENERIC(
        p_wordlength : INTEGER := 4
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(3 DOWNTO 0);
        b : IN STD_LOGIC_VECTOR(3 DOWNTO 0);
        ci : IN STD_LOGIC;
        co : OUT STD_LOGIC;
        s : OUT STD_LOGIC_VECTOR(3 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF RippleAdder0 IS
    --
    --    .. hwt-autodoc::
    --    
    COMPONENT FullAdder IS
        PORT(
            a : IN STD_LOGIC;
            b : IN STD_LOGIC;
            ci : IN STD_LOGIC;
            co : OUT STD_LOGIC;
            s : OUT STD_LOGIC
        );
    END COMPONENT;
    SIGNAL c : STD_LOGIC_VECTOR(4 DOWNTO 0);
    SIGNAL sig_fa0_a : STD_LOGIC;
    SIGNAL sig_fa0_b : STD_LOGIC;
    SIGNAL sig_fa0_ci : STD_LOGIC;
    SIGNAL sig_fa0_co : STD_LOGIC;
    SIGNAL sig_fa0_s : STD_LOGIC;
    SIGNAL sig_fa1_a : STD_LOGIC;
    SIGNAL sig_fa1_b : STD_LOGIC;
    SIGNAL sig_fa1_ci : STD_LOGIC;
    SIGNAL sig_fa1_co : STD_LOGIC;
    SIGNAL sig_fa1_s : STD_LOGIC;
    SIGNAL sig_fa2_a : STD_LOGIC;
    SIGNAL sig_fa2_b : STD_LOGIC;
    SIGNAL sig_fa2_ci : STD_LOGIC;
    SIGNAL sig_fa2_co : STD_LOGIC;
    SIGNAL sig_fa2_s : STD_LOGIC;
    SIGNAL sig_fa3_a : STD_LOGIC;
    SIGNAL sig_fa3_b : STD_LOGIC;
    SIGNAL sig_fa3_ci : STD_LOGIC;
    SIGNAL sig_fa3_co : STD_LOGIC;
    SIGNAL sig_fa3_s : STD_LOGIC;
BEGIN
    fa0_inst: FullAdder PORT MAP(
        a => sig_fa0_a,
        b => sig_fa0_b,
        ci => sig_fa0_ci,
        co => sig_fa0_co,
        s => sig_fa0_s
    );
    fa1_inst: FullAdder PORT MAP(
        a => sig_fa1_a,
        b => sig_fa1_b,
        ci => sig_fa1_ci,
        co => sig_fa1_co,
        s => sig_fa1_s
    );
    fa2_inst: FullAdder PORT MAP(
        a => sig_fa2_a,
        b => sig_fa2_b,
        ci => sig_fa2_ci,
        co => sig_fa2_co,
        s => sig_fa2_s
    );
    fa3_inst: FullAdder PORT MAP(
        a => sig_fa3_a,
        b => sig_fa3_b,
        ci => sig_fa3_ci,
        co => sig_fa3_co,
        s => sig_fa3_s
    );
    c <= sig_fa0_co & sig_fa0_co & sig_fa0_co & sig_fa0_co & ci;
    co <= c(4);
    s <= sig_fa3_s & sig_fa2_s & sig_fa1_s & sig_fa0_s;
    sig_fa0_a <= a(0);
    sig_fa0_b <= a(0);
    sig_fa0_ci <= c(0);
    sig_fa1_a <= a(1);
    sig_fa1_b <= a(1);
    sig_fa1_ci <= c(1);
    sig_fa2_a <= a(2);
    sig_fa2_b <= a(2);
    sig_fa2_ci <= c(2);
    sig_fa3_a <= a(3);
    sig_fa3_b <= a(3);
    sig_fa3_ci <= c(3);
    ASSERT p_wordlength = 4 REPORT "Generated only for this value" SEVERITY error;
END ARCHITECTURE;
