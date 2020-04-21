--Object of class Entity, "ExcludedUnit" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
--Object of class Entity, "ExcludedUnit" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;

ENTITY OnceUnit IS
    PORT (a: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF OnceUnit IS
BEGIN
    a <= '1';
END ARCHITECTURE;
--Object of class Entity, "OnceUnit" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
--Object of class Entity, "OnceUnit" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;

ENTITY u5 IS
    GENERIC (A: INTEGER := 0;
        B: INTEGER := 1
    );
    PORT (a_0: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF u5 IS
BEGIN
    a_0 <= '1';
END ARCHITECTURE;
--Object of class Entity, "u5" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;

ENTITY u7 IS
    GENERIC (A: INTEGER := 0;
        B: INTEGER := 12
    );
    PORT (a_0: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF u7 IS
BEGIN
    a_0 <= '1';
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;

ENTITY ExampleA IS
    PORT (a: OUT STD_LOGIC_VECTOR(6 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ExampleA IS
    SIGNAL sig_u0_a: STD_LOGIC;
    SIGNAL sig_u1_a: STD_LOGIC;
    SIGNAL sig_u2_a: STD_LOGIC;
    SIGNAL sig_u3_a: STD_LOGIC;
    SIGNAL sig_u4_a: STD_LOGIC;
    SIGNAL sig_u5_a_0: STD_LOGIC;
    SIGNAL sig_u6_a_0: STD_LOGIC;
    SIGNAL sig_u7_a_0: STD_LOGIC;
    COMPONENT ExcludedUnit IS
       PORT (a: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT OnceUnit IS
       PORT (a: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT u5 IS
       GENERIC (A: INTEGER := 0;
            B: INTEGER := 1
       );
       PORT (a_0: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT u7 IS
       GENERIC (A: INTEGER := 0;
            B: INTEGER := 12
       );
       PORT (a_0: OUT STD_LOGIC
       );
    END COMPONENT;

BEGIN
    u0_inst: COMPONENT ExcludedUnit
        PORT MAP (a => sig_u0_a
        );

    u1_inst: COMPONENT ExcludedUnit
        PORT MAP (a => sig_u1_a
        );

    u2_inst: COMPONENT OnceUnit
        PORT MAP (a => sig_u2_a
        );

    u3_inst: COMPONENT OnceUnit
        PORT MAP (a => sig_u3_a
        );

    u4_inst: COMPONENT OnceUnit
        PORT MAP (a => sig_u4_a
        );

    u5_inst: COMPONENT u5
        GENERIC MAP (A => 0,
            B => 1
        )
        PORT MAP (a_0 => sig_u5_a_0
        );

    u6_inst: COMPONENT u5
        GENERIC MAP (A => 0,
            B => 1
        )
        PORT MAP (a_0 => sig_u6_a_0
        );

    u7_inst: COMPONENT u7
        GENERIC MAP (A => 0,
            B => 12
        )
        PORT MAP (a_0 => sig_u7_a_0
        );

    a <= sig_u0_a & sig_u1_a & sig_u2_a & sig_u3_a & sig_u4_a & sig_u5_a_0 & sig_u6_a_0;
END ARCHITECTURE;
