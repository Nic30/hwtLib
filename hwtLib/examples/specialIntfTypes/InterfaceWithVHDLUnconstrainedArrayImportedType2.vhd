library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY InterfaceWithVHDLUnconstrainedArrayImportedType2 IS
    GENERIC (SIZE_X: INTEGER := 3
    );
    PORT (din_0: IN UNSIGNED(7 DOWNTO 0);
        din_1: IN UNSIGNED(7 DOWNTO 0);
        din_2: IN UNSIGNED(7 DOWNTO 0);
        dout: OUT mem(0 to 3)(8 downto 0)
    );
END ENTITY;

ARCHITECTURE rtl OF InterfaceWithVHDLUnconstrainedArrayImportedType2 IS
BEGIN
    dout(0) <= din_0;
    dout(1) <= din_1;
    dout(2) <= din_2;
END ARCHITECTURE;