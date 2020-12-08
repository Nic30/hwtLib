LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Basic d flip flop
--
--    :attention: using this unit is pointless because HWToolkit can automatically
--        generate such a register for any interface and datatype
--
--    .. hwt-autodoc::
--    
ENTITY DReg IS
    PORT(
        clk : IN STD_LOGIC;
        din : IN STD_LOGIC;
        dout : OUT STD_LOGIC;
        rst : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF DReg IS
    SIGNAL internReg : STD_LOGIC := '0';
    SIGNAL internReg_next : STD_LOGIC;
BEGIN
    dout <= internReg;
    assig_process_internReg: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                internReg <= '0';
            ELSE
                internReg <= internReg_next;
            END IF;
        END IF;
    END PROCESS;
    internReg_next <= din;
END ARCHITECTURE;
