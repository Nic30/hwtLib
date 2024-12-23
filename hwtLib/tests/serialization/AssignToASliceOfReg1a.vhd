LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Register where slices of next signal are set conditionally in multiple branches
--    
ENTITY AssignToASliceOfReg1a IS
    PORT(
        clk : IN STD_LOGIC;
        data_in_addr : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        data_in_data : IN STD_LOGIC_VECTOR(15 DOWNTO 0);
        data_in_rd : OUT STD_LOGIC;
        data_in_vld : IN STD_LOGIC;
        data_out : OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
        rst_n : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AssignToASliceOfReg1a IS
    SIGNAL r : STD_LOGIC_VECTOR(15 DOWNTO 0) := X"0000";
    SIGNAL r_next : STD_LOGIC_VECTOR(15 DOWNTO 0);
    SIGNAL r_next_7downto0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL r_next_15downto8 : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    data_in_rd <= '1';
    data_out <= r;
    assig_process_r: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst_n = '0' THEN
                r <= X"0000";
            ELSE
                r <= r_next;
            END IF;
        END IF;
    END PROCESS;
    r_next <= r_next_15downto8 & r_next_7downto0;
    assig_process_r_next_15downto8: PROCESS(data_in_addr, data_in_data, data_in_vld, r)
    BEGIN
        IF data_in_vld = '1' AND data_in_addr = "0" THEN
            r_next_7downto0 <= data_in_data(7 DOWNTO 0);
            r_next_15downto8 <= data_in_data(15 DOWNTO 8);
        ELSIF data_in_vld = '1' AND data_in_addr = "1" THEN
            r_next_7downto0 <= data_in_data(15 DOWNTO 8);
            r_next_15downto8 <= data_in_data(7 DOWNTO 0);
        ELSE
            r_next_7downto0 <= r(7 DOWNTO 0);
            r_next_15downto8 <= r(15 DOWNTO 8);
        END IF;
    END PROCESS;
END ARCHITECTURE;
