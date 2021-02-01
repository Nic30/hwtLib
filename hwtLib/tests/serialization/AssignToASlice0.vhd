LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Conversion between vector and bit
--    
ENTITY AssignToASlice0 IS
    PORT(
        clk : IN STD_LOGIC;
        data_in : IN STD_LOGIC;
        data_out : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
        rst_n : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AssignToASlice0 IS
BEGIN
    data_out(0) <= data_in;
END ARCHITECTURE;
