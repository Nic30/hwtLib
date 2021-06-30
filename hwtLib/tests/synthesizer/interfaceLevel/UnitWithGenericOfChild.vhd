LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY UnitWithGenericOnPort IS
    GENERIC(
        NESTED_PARAM : INTEGER := 123
    );
    PORT(
        a : IN STD_LOGIC_VECTOR(122 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF UnitWithGenericOnPort IS
    SIGNAL tmp : STD_LOGIC_VECTOR(122 DOWNTO 0);
BEGIN
    b <= tmp;
    tmp <= a;
    ASSERT NESTED_PARAM = 123 REPORT "Generated only for this value" SEVERITY error;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY UnitWithGenericOfChild IS
    PORT(
        a : IN STD_LOGIC_VECTOR(122 DOWNTO 0);
        b : OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF UnitWithGenericOfChild IS
    COMPONENT UnitWithGenericOnPort IS
        GENERIC(
            NESTED_PARAM : INTEGER := 123
        );
        PORT(
            a : IN STD_LOGIC_VECTOR(122 DOWNTO 0);
            b : OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
        );
    END COMPONENT;
    SIGNAL sig_ch_a : STD_LOGIC_VECTOR(122 DOWNTO 0);
    SIGNAL sig_ch_b : STD_LOGIC_VECTOR(122 DOWNTO 0);
    SIGNAL tmp : STD_LOGIC_VECTOR(122 DOWNTO 0);
BEGIN
    ch_inst: UnitWithGenericOnPort GENERIC MAP(
        NESTED_PARAM => 123
    ) PORT MAP(
        a => sig_ch_a,
        b => sig_ch_b
    );
    b <= tmp;
    sig_ch_a <= a;
    tmp <= b;
END ARCHITECTURE;
