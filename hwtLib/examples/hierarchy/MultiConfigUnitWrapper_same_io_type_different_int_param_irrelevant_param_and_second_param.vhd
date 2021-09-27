LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_0 IS
    GENERIC(
        ADDR_WIDTH : INTEGER := 11;
        DATA_WIDTH : INTEGER := 2;
        IRELEVANT_PARAM : INTEGER := 10
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        a_addr : IN STD_LOGIC_VECTOR(10 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        b_addr : OUT STD_LOGIC_VECTOR(10 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_0 IS
BEGIN
    b <= a;
    b_addr <= a_addr;
    ASSERT ADDR_WIDTH = 11 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT DATA_WIDTH = 2 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT IRELEVANT_PARAM = 10 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_1 IS
    GENERIC(
        ADDR_WIDTH : INTEGER := 11;
        DATA_WIDTH : INTEGER := 3;
        IRELEVANT_PARAM : INTEGER := 10
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        a_addr : IN STD_LOGIC_VECTOR(10 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
        b_addr : OUT STD_LOGIC_VECTOR(10 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_1 IS
BEGIN
    b <= a;
    b_addr <= a_addr;
    ASSERT ADDR_WIDTH = 11 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT DATA_WIDTH = 3 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT IRELEVANT_PARAM = 10 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_2 IS
    GENERIC(
        ADDR_WIDTH : INTEGER := 13;
        DATA_WIDTH : INTEGER := 2;
        IRELEVANT_PARAM : INTEGER := 10
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        a_addr : IN STD_LOGIC_VECTOR(12 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        b_addr : OUT STD_LOGIC_VECTOR(12 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_2 IS
BEGIN
    b <= a;
    b_addr <= a_addr;
    ASSERT ADDR_WIDTH = 13 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT DATA_WIDTH = 2 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT IRELEVANT_PARAM = 10 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_3 IS
    GENERIC(
        ADDR_WIDTH : INTEGER := 13;
        DATA_WIDTH : INTEGER := 3;
        IRELEVANT_PARAM : INTEGER := 10
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        a_addr : IN STD_LOGIC_VECTOR(12 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
        b_addr : OUT STD_LOGIC_VECTOR(12 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_3 IS
BEGIN
    b <= a;
    b_addr <= a_addr;
    ASSERT ADDR_WIDTH = 13 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT DATA_WIDTH = 3 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT IRELEVANT_PARAM = 10 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitWithParamWithIrrelevantParamAndAnotherParam IS
    GENERIC(
        ADDR_WIDTH : INTEGER := 11;
        DATA_WIDTH : INTEGER := 2;
        IRELEVANT_PARAM : INTEGER := 10
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        a_addr : IN STD_LOGIC_VECTOR(ADDR_WIDTH - 1 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        b_addr : OUT STD_LOGIC_VECTOR(ADDR_WIDTH - 1 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParamWithIrrelevantParamAndAnotherParam IS
    COMPONENT SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_0 IS
        GENERIC(
            ADDR_WIDTH : INTEGER := 11;
            DATA_WIDTH : INTEGER := 2;
            IRELEVANT_PARAM : INTEGER := 10
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
            a_addr : IN STD_LOGIC_VECTOR(10 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
            b_addr : OUT STD_LOGIC_VECTOR(10 DOWNTO 0)
        );
    END COMPONENT;
    COMPONENT SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_1 IS
        GENERIC(
            ADDR_WIDTH : INTEGER := 11;
            DATA_WIDTH : INTEGER := 3;
            IRELEVANT_PARAM : INTEGER := 10
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
            a_addr : IN STD_LOGIC_VECTOR(10 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
            b_addr : OUT STD_LOGIC_VECTOR(10 DOWNTO 0)
        );
    END COMPONENT;
    COMPONENT SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_2 IS
        GENERIC(
            ADDR_WIDTH : INTEGER := 13;
            DATA_WIDTH : INTEGER := 2;
            IRELEVANT_PARAM : INTEGER := 10
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
            a_addr : IN STD_LOGIC_VECTOR(12 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
            b_addr : OUT STD_LOGIC_VECTOR(12 DOWNTO 0)
        );
    END COMPONENT;
    COMPONENT SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_3 IS
        GENERIC(
            ADDR_WIDTH : INTEGER := 13;
            DATA_WIDTH : INTEGER := 3;
            IRELEVANT_PARAM : INTEGER := 10
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
            a_addr : IN STD_LOGIC_VECTOR(12 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
            b_addr : OUT STD_LOGIC_VECTOR(12 DOWNTO 0)
        );
    END COMPONENT;
BEGIN
    implementation_select: IF ADDR_WIDTH = 11 AND DATA_WIDTH = 2 AND IRELEVANT_PARAM = 10 GENERATE
        possible_variants_0_inst: SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_0 GENERIC MAP(
            ADDR_WIDTH => 11,
            DATA_WIDTH => 2,
            IRELEVANT_PARAM => 10
        ) PORT MAP(
            a => a,
            a_addr => a_addr,
            b => b,
            b_addr => b_addr
        );
    ELSIF ADDR_WIDTH = 11 AND DATA_WIDTH = 3 AND IRELEVANT_PARAM = 10 GENERATE
        possible_variants_1_inst: SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_1 GENERIC MAP(
            ADDR_WIDTH => 11,
            DATA_WIDTH => 3,
            IRELEVANT_PARAM => 10
        ) PORT MAP(
            a => a,
            a_addr => a_addr,
            b => b,
            b_addr => b_addr
        );
    ELSIF ADDR_WIDTH = 13 AND DATA_WIDTH = 2 AND IRELEVANT_PARAM = 10 GENERATE
        possible_variants_2_inst: SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_2 GENERIC MAP(
            ADDR_WIDTH => 13,
            DATA_WIDTH => 2,
            IRELEVANT_PARAM => 10
        ) PORT MAP(
            a => a,
            a_addr => a_addr,
            b => b,
            b_addr => b_addr
        );
    ELSIF ADDR_WIDTH = 13 AND DATA_WIDTH = 3 AND IRELEVANT_PARAM = 10 GENERATE
        possible_variants_3_inst: SimpleUnitWithParamWithIrrelevantParamAndAnotherParam_3 GENERIC MAP(
            ADDR_WIDTH => 13,
            DATA_WIDTH => 3,
            IRELEVANT_PARAM => 10
        ) PORT MAP(
            a => a,
            a_addr => a_addr,
            b => b,
            b_addr => b_addr
        );
    ELSE GENERATE
        ASSERT FALSE REPORT "The component was generated for this generic/params combination" SEVERITY failure;
    END GENERATE;
END ARCHITECTURE;
