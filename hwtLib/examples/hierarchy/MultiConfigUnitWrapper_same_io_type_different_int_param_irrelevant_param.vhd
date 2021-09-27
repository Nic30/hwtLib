LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitWithParamWithIrrelevantParam_0 IS
    GENERIC(
        DATA_WIDTH : INTEGER := 2;
        IRELEVANT_PARAM : INTEGER := 10
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParamWithIrrelevantParam_0 IS
BEGIN
    b <= a;
    ASSERT DATA_WIDTH = 2 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT IRELEVANT_PARAM = 10 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitWithParamWithIrrelevantParam_1 IS
    GENERIC(
        DATA_WIDTH : INTEGER := 3;
        IRELEVANT_PARAM : INTEGER := 10
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParamWithIrrelevantParam_1 IS
BEGIN
    b <= a;
    ASSERT DATA_WIDTH = 3 REPORT "Generated only for this value" SEVERITY failure;
    ASSERT IRELEVANT_PARAM = 10 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitWithParamWithIrrelevantParam IS
    GENERIC(
        DATA_WIDTH : INTEGER := 2;
        IRELEVANT_PARAM : INTEGER := 10
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParamWithIrrelevantParam IS
    COMPONENT SimpleUnitWithParamWithIrrelevantParam_0 IS
        GENERIC(
            DATA_WIDTH : INTEGER := 2;
            IRELEVANT_PARAM : INTEGER := 10
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0)
        );
    END COMPONENT;
    COMPONENT SimpleUnitWithParamWithIrrelevantParam_1 IS
        GENERIC(
            DATA_WIDTH : INTEGER := 3;
            IRELEVANT_PARAM : INTEGER := 10
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0)
        );
    END COMPONENT;
BEGIN
    implementation_select: IF DATA_WIDTH = 2 AND IRELEVANT_PARAM = 10 GENERATE
        possible_variants_0_inst: SimpleUnitWithParamWithIrrelevantParam_0 GENERIC MAP(
            DATA_WIDTH => 2,
            IRELEVANT_PARAM => 10
        ) PORT MAP(
            a => a,
            b => b
        );
    ELSIF DATA_WIDTH = 3 AND IRELEVANT_PARAM = 10 GENERATE
        possible_variants_1_inst: SimpleUnitWithParamWithIrrelevantParam_1 GENERIC MAP(
            DATA_WIDTH => 3,
            IRELEVANT_PARAM => 10
        ) PORT MAP(
            a => a,
            b => b
        );
    ELSE GENERATE
        ASSERT FALSE REPORT "The component was generated for this generic/params combination" SEVERITY failure;
    END GENERATE;
END ARCHITECTURE;
