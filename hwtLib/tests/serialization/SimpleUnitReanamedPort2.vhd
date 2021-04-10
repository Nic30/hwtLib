LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitReanamedPort2 IS
    PORT(
        a_in_hdl : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        a_in_hdl_ready : OUT STD_LOGIC;
        a_in_hdl_valid : IN STD_LOGIC;
        b_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_rd : IN STD_LOGIC;
        b_vld : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitReanamedPort2 IS
BEGIN
    a_in_hdl_ready <= b_rd;
    b_data <= a_in_hdl;
    b_vld <= a_in_hdl_valid;
END ARCHITECTURE;
