LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitReanamedPort1 IS
    PORT(
        a_in_hdl_data : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        a_in_hdl_rd : OUT STD_LOGIC;
        a_in_hdl_vld : IN STD_LOGIC;
        b_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_rd : IN STD_LOGIC;
        b_vld : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitReanamedPort1 IS
BEGIN
    a_in_hdl_rd <= b_rd;
    b_data <= a_in_hdl_data;
    b_vld <= a_in_hdl_vld;
END ARCHITECTURE;
