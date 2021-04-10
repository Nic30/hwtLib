LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitReanamedPort0 IS
    PORT(
        a_in_hdl : IN STD_LOGIC;
        b : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitReanamedPort0 IS
BEGIN
    b <= a_in_hdl;
END ARCHITECTURE;
