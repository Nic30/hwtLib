--
--    .. hwt-schematic::
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY AsyncResetReg IS
    PORT (clk: IN STD_LOGIC;
        din: IN STD_LOGIC;
        dout: OUT STD_LOGIC;
        rst: IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AsyncResetReg IS
    SIGNAL internReg: STD_LOGIC := '0';
BEGIN
    dout <= internReg;
    assig_process_internReg: PROCESS (clk, rst)
    BEGIN
        IF rst = '1' THEN
            internReg <= '0';
        ELSIF RISING_EDGE(clk) THEN
            internReg <= din;
        END IF;
    END PROCESS;

END ARCHITECTURE;