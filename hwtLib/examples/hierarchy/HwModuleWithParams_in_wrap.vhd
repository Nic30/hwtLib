LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--.. hwt-autodoc::
ENTITY HwModuleWithParams_0 IS
    GENERIC(
        DATA_WIDTH : INTEGER := 64
    );
    PORT(
        din_data : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        din_vld : IN STD_LOGIC;
        dout_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        dout_vld : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF HwModuleWithParams_0 IS
BEGIN
    dout_data <= din_data;
    dout_vld <= din_vld;
    ASSERT DATA_WIDTH = 64 REPORT "Generated only for this value" SEVERITY failure;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--.. hwt-autodoc::
ENTITY HwModuleWithParams IS
    PORT(
        din_data : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        din_vld : IN STD_LOGIC;
        dout_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        dout_vld : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF HwModuleWithParams IS
    --
    --.. hwt-autodoc::
    COMPONENT HwModuleWithParams_0 IS
        GENERIC(
            DATA_WIDTH : INTEGER := 64
        );
        PORT(
            din_data : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
            din_vld : IN STD_LOGIC;
            dout_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
            dout_vld : OUT STD_LOGIC
        );
    END COMPONENT;
    SIGNAL sig_baseModule_din_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_baseModule_din_vld : STD_LOGIC;
    SIGNAL sig_baseModule_dout_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_baseModule_dout_vld : STD_LOGIC;
BEGIN
    baseModule_inst: HwModuleWithParams_0 GENERIC MAP(
        DATA_WIDTH => 64
    ) PORT MAP(
        din_data => sig_baseModule_din_data,
        din_vld => sig_baseModule_din_vld,
        dout_data => sig_baseModule_dout_data,
        dout_vld => sig_baseModule_dout_vld
    );
    dout_data <= sig_baseModule_dout_data;
    dout_vld <= sig_baseModule_dout_vld;
    sig_baseModule_din_data <= din_data;
    sig_baseModule_din_vld <= din_vld;
END ARCHITECTURE;
