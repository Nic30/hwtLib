LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Vector parts driven from multi branch statement
--    
ENTITY AssignToASlice2 IS
    PORT(
        clk : IN STD_LOGIC;
        data_in : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        data_out : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
        rst_n : IN STD_LOGIC;
        swap : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AssignToASlice2 IS
    SIGNAL data_out_0 : STD_LOGIC;
    SIGNAL data_out_1 : STD_LOGIC;
    SIGNAL data_out_2 : STD_LOGIC;
BEGIN
    data_out <= data_out_2 & data_out_1 & data_out_0;
    assig_process_data_out_0: PROCESS(data_in, swap)
    BEGIN
        IF swap = '1' THEN
            data_out_0 <= data_in(1);
            data_out_1 <= data_in(0);
            data_out_2 <= data_in(0);
        ELSE
            data_out_0 <= data_in(0);
            data_out_1 <= data_in(1);
            data_out_2 <= data_in(1);
        END IF;
    END PROCESS;
END ARCHITECTURE;
