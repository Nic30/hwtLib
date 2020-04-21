LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;

ENTITY InterfaceWithVHDLUnconstrainedArrayImportedType IS
    GENERIC (SIZE_X: INTEGER := 3
    );
    PORT (din: IN mem(0 to 3)(8 downto 0);
        dout_0: OUT UNSIGNED(7 DOWNTO 0);
        dout_1: OUT UNSIGNED(7 DOWNTO 0);
        dout_2: OUT UNSIGNED(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF InterfaceWithVHDLUnconstrainedArrayImportedType IS
BEGIN
    dout_0 <= din(0);
    dout_1 <= din(1);
    dout_2 <= din(2);
END ARCHITECTURE;