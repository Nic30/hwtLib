LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY Assign1bVec IS
    PORT(
        clk : IN STD_LOGIC;
        i0 : IN STD_LOGIC;
        i1v : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        o0 : OUT STD_LOGIC;
        o1v : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
        o2 : OUT STD_LOGIC;
        o3v : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
        rst_n : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF Assign1bVec IS
BEGIN
    o0 <= i0;
    o1v(0) <= i0;
    o2 <= i1v(0);
    o3v <= i1v;
END ARCHITECTURE;
