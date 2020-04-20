--
--    This is comment for SimpleComentedUnit entity, it will be rendered before entity as comment.
--    Do not forget that class inheritance does apply for docstring as well.
--
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleComentedUnit IS
    PORT (a: IN STD_LOGIC;
        b: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleComentedUnit IS

BEGIN

    b <= a;

END ARCHITECTURE;
