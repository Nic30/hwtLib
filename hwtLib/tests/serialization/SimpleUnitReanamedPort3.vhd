LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitReanamedPort3 IS
    PORT(
        b_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_rd : IN STD_LOGIC;
        b_vld : OUT STD_LOGIC;
        data : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        rd : OUT STD_LOGIC;
        vld : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitReanamedPort3 IS
BEGIN
    b_data <= data;
    b_vld <= vld;
    rd <= b_rd;
END ARCHITECTURE;
