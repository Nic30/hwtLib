LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Double Data Rate register
--
--    .. hwt-autodoc::
--    
ENTITY DDR_Reg IS
    PORT(
        clk : IN STD_LOGIC;
        din : IN STD_LOGIC;
        dout : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        rst : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF DDR_Reg IS
    SIGNAL internReg : STD_LOGIC := '0';
    SIGNAL internReg_0 : STD_LOGIC := '0';
BEGIN
    dout <= internReg & internReg_0;
    assig_process_internReg: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            internReg <= din;
        END IF;
    END PROCESS;
    assig_process_internReg_0: PROCESS(clk)
    BEGIN
        IF FALLING_EDGE(clk) THEN
            internReg_0 <= din;
        END IF;
    END PROCESS;
END ARCHITECTURE;
