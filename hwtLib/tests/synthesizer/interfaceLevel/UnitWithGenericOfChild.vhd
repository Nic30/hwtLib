library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY ch IS
    GENERIC (NESTED_PARAM: INTEGER := 123
    );
    PORT (a: IN STD_LOGIC_VECTOR(122 DOWNTO 0);
        b: OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ch IS
    SIGNAL tmp: STD_LOGIC_VECTOR(122 DOWNTO 0);
BEGIN
    b <= tmp;
    tmp <= a;
END ARCHITECTURE;
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY UnitWithGenericOfChild IS
    PORT (a: IN STD_LOGIC_VECTOR(122 DOWNTO 0);
        b: OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF UnitWithGenericOfChild IS
    SIGNAL sig_ch_a: STD_LOGIC_VECTOR(122 DOWNTO 0);
    SIGNAL sig_ch_b: STD_LOGIC_VECTOR(122 DOWNTO 0);
    SIGNAL tmp: STD_LOGIC_VECTOR(122 DOWNTO 0);
    COMPONENT ch IS
       GENERIC (NESTED_PARAM: INTEGER := 123
       );
       PORT (a: IN STD_LOGIC_VECTOR(122 DOWNTO 0);
            b: OUT STD_LOGIC_VECTOR(122 DOWNTO 0)
       );
    END COMPONENT;

BEGIN
    ch_inst: COMPONENT ch
        GENERIC MAP (NESTED_PARAM => 123
        )
        PORT MAP (a => sig_ch_a,
            b => sig_ch_b
        );

    b <= tmp;
    sig_ch_a <= a;
    tmp <= b;
END ARCHITECTURE;
