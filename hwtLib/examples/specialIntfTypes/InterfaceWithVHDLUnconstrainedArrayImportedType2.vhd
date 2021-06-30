LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY InterfaceWithVHDLUnconstrainedArrayImportedType2 IS
    GENERIC(
        SIZE_X : INTEGER := 3
    );
    PORT(
        din_0 : IN UNSIGNED(7 DOWNTO 0);
        din_1 : IN UNSIGNED(7 DOWNTO 0);
        din_2 : IN UNSIGNED(7 DOWNTO 0);
        dout : OUT mem(0 TO 3)(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF InterfaceWithVHDLUnconstrainedArrayImportedType2 IS
BEGIN
    dout(0) <= din_0;
    dout(1) <= din_1;
    dout(2) <= din_2;
    ASSERT SIZE_X = 3 REPORT "Generated only for this value" SEVERITY error;
END ARCHITECTURE;
