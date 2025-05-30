LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Something not assigned by index at the beggining and then whole signal assigned.
--    
ENTITY AssignToASliceOfReg3c IS
    PORT(
        clk : IN STD_LOGIC;
        data_in_addr : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        data_in_data : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        data_in_mask : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        data_in_rd : OUT STD_LOGIC;
        data_in_vld : IN STD_LOGIC;
        data_out : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
        rst_n : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AssignToASliceOfReg3c IS
    SIGNAL r : STD_LOGIC_VECTOR(31 DOWNTO 0) := X"00000000";
    SIGNAL r_next : STD_LOGIC_VECTOR(31 DOWNTO 0);
    SIGNAL r_next_7downto0 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL r_next_15downto8 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL r_next_23downto16 : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL r_next_31downto24 : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    data_in_rd <= '1';
    data_out <= r;
    assig_process_r: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst_n = '0' THEN
                r <= X"00000000";
            ELSE
                r <= r_next;
            END IF;
        END IF;
    END PROCESS;
    r_next <= r_next_31downto24 & r_next_23downto16 & r_next_15downto8 & r_next_7downto0;
    assig_process_r_next_15downto8: PROCESS(data_in_addr, data_in_data, r)
    BEGIN
        CASE data_in_addr IS
            WHEN "01" =>
                r_next_15downto8 <= data_in_data;
                r_next_7downto0 <= r(7 DOWNTO 0);
                r_next_23downto16 <= r(23 DOWNTO 16);
                r_next_31downto24 <= r(31 DOWNTO 24);
            WHEN "10" =>
                r_next_23downto16 <= data_in_data;
                r_next_7downto0 <= r(7 DOWNTO 0);
                r_next_15downto8 <= r(15 DOWNTO 8);
                r_next_31downto24 <= r(31 DOWNTO 24);
            WHEN "11" =>
                r_next_31downto24 <= data_in_data;
                r_next_7downto0 <= r(7 DOWNTO 0);
                r_next_15downto8 <= r(15 DOWNTO 8);
                r_next_23downto16 <= r(23 DOWNTO 16);
            WHEN OTHERS =>
                r_next_7downto0 <= X"7B";
                r_next_15downto8 <= X"00";
                r_next_23downto16 <= X"00";
                r_next_31downto24 <= X"00";
        END CASE;
    END PROCESS;
END ARCHITECTURE;
