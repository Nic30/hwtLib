
--dynamically generated, for example loaded from file or builded from unit content
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleComentedUnit3 IS
    PORT (a: IN STD_LOGIC;
        b: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleComentedUnit3 IS

BEGIN

    b <= a;

END ARCHITECTURE;
