LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Simple parametrized unit.
--
--    .. hwt-schematic::
--    
ENTITY SimpleUnitWithParam_0 IS
    GENERIC(
        DATA_WIDTH : INTEGER := 2
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParam_0 IS
BEGIN
    b <= a;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Simple parametrized unit.
--
--    .. hwt-schematic::
--    
ENTITY SimpleUnitWithParam_1 IS
    GENERIC(
        DATA_WIDTH : INTEGER := 3
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParam_1 IS
BEGIN
    b <= a;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Simple parametrized unit.
--
--    .. hwt-schematic::
--    
ENTITY SimpleUnitWithParam IS
    GENERIC(
        DATA_WIDTH : INTEGER := 2
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitWithParam IS
    --
    --    Simple parametrized unit.
    --
    --    .. hwt-schematic::
    --    
    COMPONENT SimpleUnitWithParam_0 IS
        GENERIC(
            DATA_WIDTH : INTEGER := 2
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(1 DOWNTO 0)
        );
    END COMPONENT;
    --
    --    Simple parametrized unit.
    --
    --    .. hwt-schematic::
    --    
    COMPONENT SimpleUnitWithParam_1 IS
        GENERIC(
            DATA_WIDTH : INTEGER := 3
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(2 DOWNTO 0)
        );
    END COMPONENT;
BEGIN
    implementation_select: IF DATA_WIDTH = 2 GENERATE
        possible_variants_0_inst: SimpleUnitWithParam_0 GENERIC MAP(
            DATA_WIDTH => 2
        ) PORT MAP(
            a => a,
            b => b
        );
    ELSIF DATA_WIDTH = 3 GENERATE
        possible_variants_1_inst: SimpleUnitWithParam_1 GENERIC MAP(
            DATA_WIDTH => 3
        ) PORT MAP(
            a => a,
            b => b
        );
    END GENERATE;
END ARCHITECTURE;
