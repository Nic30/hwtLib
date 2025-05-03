LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY ExampleHBitsMul1c IS
    PORT(
        a : IN SIGNED(7 DOWNTO 0);
        b : IN SIGNED(7 DOWNTO 0);
        c : IN SIGNED(15 DOWNTO 0);
        res : OUT SIGNED(15 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ExampleHBitsMul1c IS
BEGIN
    res <= UNSIGNED(a) * UNSIGNED(b) + c;
END ARCHITECTURE;
