LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY IndexOps IS
    PORT(
        s_in : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_in2 : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_in3 : IN STD_LOGIC_VECTOR(15 DOWNTO 0);
        s_in4a : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_in4b : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out2 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out3 : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out4 : OUT STD_LOGIC_VECTOR(15 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF IndexOps IS
BEGIN
    s_out <= s_in(3 DOWNTO 0) & X"2";
    s_out2 <= s_in2(7 DOWNTO 4) & s_in2(3 DOWNTO 0);
    s_out3 <= s_in3(7 DOWNTO 0);
    s_out4 <= s_in4b & s_in4a;
END ARCHITECTURE;
