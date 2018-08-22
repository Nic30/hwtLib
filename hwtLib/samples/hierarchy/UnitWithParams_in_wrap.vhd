library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY baseUnit IS
    GENERIC (DATA_WIDTH: INTEGER := 64;
        din_DATA_WIDTH: INTEGER := 64;
        dout_DATA_WIDTH: INTEGER := 64
    );
    PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
        din_vld: IN STD_LOGIC;
        dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
        dout_vld: OUT STD_LOGIC
    );
END baseUnit;

ARCHITECTURE rtl OF baseUnit IS
BEGIN
    dout_data <= din_data;
    dout_vld <= din_vld;
END ARCHITECTURE rtl;
--
--    Class which creates wrapper around original unit instance,
--    original unit will be sotred inside as subunit named baseUnit
--
--    :note: This is also example of lazy loaded interfaces
--        and generating of external interfaces based on internal stucture.
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY UnitWithParams IS
    GENERIC (DATA_WIDTH: INTEGER := 64;
        baseUnit_din_DATA_WIDTH: INTEGER := 64;
        baseUnit_dout_DATA_WIDTH: INTEGER := 64
    );
    PORT (din_data: IN STD_LOGIC_VECTOR(baseUnit_din_DATA_WIDTH - 1 DOWNTO 0);
        din_vld: IN STD_LOGIC;
        dout_data: OUT STD_LOGIC_VECTOR(baseUnit_dout_DATA_WIDTH - 1 DOWNTO 0);
        dout_vld: OUT STD_LOGIC
    );
END UnitWithParams;

ARCHITECTURE rtl OF UnitWithParams IS
    SIGNAL sig_baseUnit_din_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_baseUnit_din_vld: STD_LOGIC;
    SIGNAL sig_baseUnit_dout_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_baseUnit_dout_vld: STD_LOGIC;
    COMPONENT baseUnit IS
       GENERIC (DATA_WIDTH: INTEGER := 64;
            din_DATA_WIDTH: INTEGER := 64;
            dout_DATA_WIDTH: INTEGER := 64
       );
       PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
            din_vld: IN STD_LOGIC;
            dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
            dout_vld: OUT STD_LOGIC
       );
    END COMPONENT;

BEGIN
    baseUnit_inst: COMPONENT baseUnit
        GENERIC MAP (DATA_WIDTH => 64,
            din_DATA_WIDTH => 64,
            dout_DATA_WIDTH => 64
        )
        PORT MAP (din_data => sig_baseUnit_din_data,
            din_vld => sig_baseUnit_din_vld,
            dout_data => sig_baseUnit_dout_data,
            dout_vld => sig_baseUnit_dout_vld
        );

    dout_data <= sig_baseUnit_dout_data;
    dout_vld <= sig_baseUnit_dout_vld;
    sig_baseUnit_din_data <= din_data;
    sig_baseUnit_din_vld <= din_vld;
END ARCHITECTURE rtl;