LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY OnceHwModule IS
    PORT(
        a : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF OnceHwModule IS
BEGIN
    a <= '1';
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ParamsUniqHwModule IS
    GENERIC(
        A : INTEGER := 0;
        B : INTEGER := 1
    );
    PORT(
        a_0 : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF ParamsUniqHwModule IS
BEGIN
    a_0 <= '1';
    ASSERT A = 0 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT B = 1 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ParamsUniqHwModule_0 IS
    GENERIC(
        A : INTEGER := 0;
        B : INTEGER := 12
    );
    PORT(
        a_0 : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF ParamsUniqHwModule_0 IS
BEGIN
    a_0 <= '1';
    ASSERT A = 0 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT B = 12 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ExampleA IS
    PORT(
        a : OUT STD_LOGIC_VECTOR(6 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ExampleA IS
    COMPONENT ExcludedHwModule IS
        PORT(
            a : OUT STD_LOGIC
        );
    END COMPONENT;
    COMPONENT OnceHwModule IS
        PORT(
            a : OUT STD_LOGIC
        );
    END COMPONENT;
    COMPONENT ParamsUniqHwModule IS
        GENERIC(
            A : INTEGER := 0;
            B : INTEGER := 1
        );
        PORT(
            a_0 : OUT STD_LOGIC
        );
    END COMPONENT;
    COMPONENT ParamsUniqHwModule_0 IS
        GENERIC(
            A : INTEGER := 0;
            B : INTEGER := 12
        );
        PORT(
            a_0 : OUT STD_LOGIC
        );
    END COMPONENT;
    SIGNAL sig_m0_a : STD_LOGIC;
    SIGNAL sig_m1_a : STD_LOGIC;
    SIGNAL sig_m2_a : STD_LOGIC;
    SIGNAL sig_m3_a : STD_LOGIC;
    SIGNAL sig_m4_a : STD_LOGIC;
    SIGNAL sig_m5_a : STD_LOGIC;
    SIGNAL sig_m6_a : STD_LOGIC;
    SIGNAL sig_m7_a : STD_LOGIC;
BEGIN
    m0_inst: ExcludedHwModule PORT MAP(
        a => sig_m0_a
    );
    m1_inst: ExcludedHwModule PORT MAP(
        a => sig_m1_a
    );
    m2_inst: OnceHwModule PORT MAP(
        a => sig_m2_a
    );
    m3_inst: OnceHwModule PORT MAP(
        a => sig_m3_a
    );
    m4_inst: OnceHwModule PORT MAP(
        a => sig_m4_a
    );
    m5_inst: ParamsUniqHwModule GENERIC MAP(
        A => 0,
        B => 1
    ) PORT MAP(
        a_0 => sig_m5_a
    );
    m6_inst: ParamsUniqHwModule GENERIC MAP(
        A => 0,
        B => 1
    ) PORT MAP(
        a_0 => sig_m6_a
    );
    m7_inst: ParamsUniqHwModule_0 GENERIC MAP(
        A => 0,
        B => 12
    ) PORT MAP(
        a_0 => sig_m7_a
    );
    a <= sig_m0_a & sig_m1_a & sig_m2_a & sig_m3_a & sig_m4_a & sig_m5_a & sig_m6_a;
END ARCHITECTURE;
