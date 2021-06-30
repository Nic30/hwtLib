LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY OnceUnit IS
    PORT(
        a : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF OnceUnit IS
BEGIN
    a <= '1';
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ParamsUniqUnit IS
    GENERIC(
        A : INTEGER := 0;
        B : INTEGER := 1
    );
    PORT(
        a_0 : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF ParamsUniqUnit IS
BEGIN
    a_0 <= '1';
    ASSERT A = 0 REPORT "Generated only for this value" SEVERITY error;
    ASSERT B = 1 REPORT "Generated only for this value" SEVERITY error;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ParamsUniqUnit_0 IS
    GENERIC(
        A : INTEGER := 0;
        B : INTEGER := 12
    );
    PORT(
        a_0 : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF ParamsUniqUnit_0 IS
BEGIN
    a_0 <= '1';
    ASSERT A = 0 REPORT "Generated only for this value" SEVERITY error;
    ASSERT B = 12 REPORT "Generated only for this value" SEVERITY error;
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
    COMPONENT ExcludedUnit IS
        PORT(
            a : OUT STD_LOGIC
        );
    END COMPONENT;
    COMPONENT OnceUnit IS
        PORT(
            a : OUT STD_LOGIC
        );
    END COMPONENT;
    COMPONENT ParamsUniqUnit IS
        GENERIC(
            A : INTEGER := 0;
            B : INTEGER := 1
        );
        PORT(
            a_0 : OUT STD_LOGIC
        );
    END COMPONENT;
    COMPONENT ParamsUniqUnit_0 IS
        GENERIC(
            A : INTEGER := 0;
            B : INTEGER := 12
        );
        PORT(
            a_0 : OUT STD_LOGIC
        );
    END COMPONENT;
    SIGNAL sig_u0_a : STD_LOGIC;
    SIGNAL sig_u1_a : STD_LOGIC;
    SIGNAL sig_u2_a : STD_LOGIC;
    SIGNAL sig_u3_a : STD_LOGIC;
    SIGNAL sig_u4_a : STD_LOGIC;
    SIGNAL sig_u5_a : STD_LOGIC;
    SIGNAL sig_u6_a : STD_LOGIC;
    SIGNAL sig_u7_a : STD_LOGIC;
BEGIN
    u0_inst: ExcludedUnit PORT MAP(
        a => sig_u0_a
    );
    u1_inst: ExcludedUnit PORT MAP(
        a => sig_u1_a
    );
    u2_inst: OnceUnit PORT MAP(
        a => sig_u2_a
    );
    u3_inst: OnceUnit PORT MAP(
        a => sig_u3_a
    );
    u4_inst: OnceUnit PORT MAP(
        a => sig_u4_a
    );
    u5_inst: ParamsUniqUnit GENERIC MAP(
        A => 0,
        B => 1
    ) PORT MAP(
        a_0 => sig_u5_a
    );
    u6_inst: ParamsUniqUnit GENERIC MAP(
        A => 0,
        B => 1
    ) PORT MAP(
        a_0 => sig_u6_a
    );
    u7_inst: ParamsUniqUnit_0 GENERIC MAP(
        A => 0,
        B => 12
    ) PORT MAP(
        a_0 => sig_u7_a
    );
    a <= sig_u0_a & sig_u1_a & sig_u2_a & sig_u3_a & sig_u4_a & sig_u5_a & sig_u6_a;
END ARCHITECTURE;
