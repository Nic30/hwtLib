--single line
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleComentedUnit2 IS
    PORT (a: IN STD_LOGIC;
        b: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleComentedUnit2 IS

BEGIN

    b <= a;

END ARCHITECTURE;
