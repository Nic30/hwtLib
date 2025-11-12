LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--This is comment for SimpleComentedHwModule entity, it will be rendered before entity as comment.
--Do not forget that class inheritance does apply for docstring as well.
ENTITY SimpleComentedHwModule IS
    PORT(
        a : IN STD_LOGIC;
        b : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleComentedHwModule IS
BEGIN
    b <= a;
END ARCHITECTURE;
