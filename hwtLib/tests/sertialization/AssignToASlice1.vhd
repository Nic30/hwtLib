LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Vector parts driven by expr
--    
ENTITY AssignToASlice1 IS
    PORT(
        clk : IN STD_LOGIC;
        data_in : IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        data_out : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
        rst_n : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AssignToASlice1 IS
BEGIN
    data_out <= data_in(2) & data_in(1) & data_in(0);
END ARCHITECTURE;
