LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    RAM where each port has an independet clock.
--    It can be configured to true dual port RAM etc.
--    It can also be configured to have write mask or to be composed from multiple smaller memories.
--
--    :note: write-first variant
--
--    .. hwt-autodoc::
--    
ENTITY RamMultiClock IS
    GENERIC(
        ADDR_WIDTH : INTEGER := 8;
        DATA_WIDTH : INTEGER := 64;
        HAS_BE : BOOLEAN := FALSE;
        INIT_DATA : STRING := "None";
        MAX_BLOCK_DATA_WIDTH : STRING := "None";
        PORT_CNT : INTEGER := 2
    );
    PORT(
        port_0_addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        port_0_clk : IN STD_LOGIC;
        port_0_din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        port_0_dout : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        port_0_en : IN STD_LOGIC;
        port_0_we : IN STD_LOGIC;
        port_1_addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        port_1_clk : IN STD_LOGIC;
        port_1_din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        port_1_dout : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        port_1_en : IN STD_LOGIC;
        port_1_we : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF RamMultiClock IS
    TYPE arr_t_0 IS ARRAY (255 DOWNTO 0) OF STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL ram_memory : arr_t_0;
BEGIN
    assig_process_port_0_dout: PROCESS(port_0_clk)
    BEGIN
        IF RISING_EDGE(port_0_clk) THEN
            IF port_0_en = '1' THEN
                IF port_0_we = '1' THEN
                    ram_memory(TO_INTEGER(UNSIGNED(port_0_addr))) <= port_0_din;
                END IF;
                port_0_dout <= ram_memory(TO_INTEGER(UNSIGNED(port_0_addr)));
            ELSE
                port_0_dout <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
            END IF;
        END IF;
    END PROCESS;
    assig_process_port_1_dout: PROCESS(port_1_clk)
    BEGIN
        IF RISING_EDGE(port_1_clk) THEN
            IF port_1_en = '1' THEN
                IF port_1_we = '1' THEN
                    ram_memory(TO_INTEGER(UNSIGNED(port_1_addr))) <= port_1_din;
                END IF;
                port_1_dout <= ram_memory(TO_INTEGER(UNSIGNED(port_1_addr)));
            ELSE
                port_1_dout <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
            END IF;
        END IF;
    END PROCESS;
    ASSERT ADDR_WIDTH = 8 REPORT "Generated only for this value" SEVERITY error;
    ASSERT DATA_WIDTH = 64 REPORT "Generated only for this value" SEVERITY error;
    ASSERT HAS_BE = FALSE REPORT "Generated only for this value" SEVERITY error;
    ASSERT INIT_DATA = "None" REPORT "Generated only for this value" SEVERITY error;
    ASSERT MAX_BLOCK_DATA_WIDTH = "None" REPORT "Generated only for this value" SEVERITY error;
    ASSERT PORT_CNT = 2 REPORT "Generated only for this value" SEVERITY error;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-autodoc::
--    
ENTITY GroupOfBlockrams IS
    GENERIC(
        ADDR_WIDTH : INTEGER := 8;
        DATA_WIDTH : INTEGER := 64
    );
    PORT(
        addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        clk : IN STD_LOGIC;
        en : IN STD_LOGIC;
        in_r_a : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        in_r_b : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        in_w_a : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        in_w_b : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        out_r_a : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        out_r_b : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        out_w_a : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        out_w_b : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        we : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF GroupOfBlockrams IS
    --
    --    RAM where each port has an independet clock.
    --    It can be configured to true dual port RAM etc.
    --    It can also be configured to have write mask or to be composed from multiple smaller memories.
    --
    --    :note: write-first variant
    --
    --    .. hwt-autodoc::
    --    
    COMPONENT RamMultiClock IS
        GENERIC(
            ADDR_WIDTH : INTEGER := 8;
            DATA_WIDTH : INTEGER := 64;
            HAS_BE : BOOLEAN := FALSE;
            INIT_DATA : STRING := "None";
            MAX_BLOCK_DATA_WIDTH : STRING := "None";
            PORT_CNT : INTEGER := 2
        );
        PORT(
            port_0_addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            port_0_clk : IN STD_LOGIC;
            port_0_din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
            port_0_dout : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
            port_0_en : IN STD_LOGIC;
            port_0_we : IN STD_LOGIC;
            port_1_addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            port_1_clk : IN STD_LOGIC;
            port_1_din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
            port_1_dout : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
            port_1_en : IN STD_LOGIC;
            port_1_we : IN STD_LOGIC
        );
    END COMPONENT;
    SIGNAL sig_bramR_port_0_addr : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramR_port_0_clk : STD_LOGIC;
    SIGNAL sig_bramR_port_0_din : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_port_0_dout : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_port_0_en : STD_LOGIC;
    SIGNAL sig_bramR_port_0_we : STD_LOGIC;
    SIGNAL sig_bramR_port_1_addr : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramR_port_1_clk : STD_LOGIC;
    SIGNAL sig_bramR_port_1_din : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_port_1_dout : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_port_1_en : STD_LOGIC;
    SIGNAL sig_bramR_port_1_we : STD_LOGIC;
    SIGNAL sig_bramW_port_0_addr : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramW_port_0_clk : STD_LOGIC;
    SIGNAL sig_bramW_port_0_din : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_port_0_dout : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_port_0_en : STD_LOGIC;
    SIGNAL sig_bramW_port_0_we : STD_LOGIC;
    SIGNAL sig_bramW_port_1_addr : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramW_port_1_clk : STD_LOGIC;
    SIGNAL sig_bramW_port_1_din : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_port_1_dout : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_port_1_en : STD_LOGIC;
    SIGNAL sig_bramW_port_1_we : STD_LOGIC;
BEGIN
    bramR_inst: RamMultiClock GENERIC MAP(
        ADDR_WIDTH => 8,
        DATA_WIDTH => 64,
        HAS_BE => FALSE,
        INIT_DATA => "None",
        MAX_BLOCK_DATA_WIDTH => "None",
        PORT_CNT => 2
    ) PORT MAP(
        port_0_addr => sig_bramR_port_0_addr,
        port_0_clk => sig_bramR_port_0_clk,
        port_0_din => sig_bramR_port_0_din,
        port_0_dout => sig_bramR_port_0_dout,
        port_0_en => sig_bramR_port_0_en,
        port_0_we => sig_bramR_port_0_we,
        port_1_addr => sig_bramR_port_1_addr,
        port_1_clk => sig_bramR_port_1_clk,
        port_1_din => sig_bramR_port_1_din,
        port_1_dout => sig_bramR_port_1_dout,
        port_1_en => sig_bramR_port_1_en,
        port_1_we => sig_bramR_port_1_we
    );
    bramW_inst: RamMultiClock GENERIC MAP(
        ADDR_WIDTH => 8,
        DATA_WIDTH => 64,
        HAS_BE => FALSE,
        INIT_DATA => "None",
        MAX_BLOCK_DATA_WIDTH => "None",
        PORT_CNT => 2
    ) PORT MAP(
        port_0_addr => sig_bramW_port_0_addr,
        port_0_clk => sig_bramW_port_0_clk,
        port_0_din => sig_bramW_port_0_din,
        port_0_dout => sig_bramW_port_0_dout,
        port_0_en => sig_bramW_port_0_en,
        port_0_we => sig_bramW_port_0_we,
        port_1_addr => sig_bramW_port_1_addr,
        port_1_clk => sig_bramW_port_1_clk,
        port_1_din => sig_bramW_port_1_din,
        port_1_dout => sig_bramW_port_1_dout,
        port_1_en => sig_bramW_port_1_en,
        port_1_we => sig_bramW_port_1_we
    );
    out_r_a <= sig_bramR_port_0_dout;
    out_r_b <= sig_bramR_port_1_dout;
    out_w_a <= sig_bramW_port_0_dout;
    out_w_b <= sig_bramW_port_1_dout;
    sig_bramR_port_0_addr <= addr;
    sig_bramR_port_0_clk <= clk;
    sig_bramR_port_0_din <= in_r_a;
    sig_bramR_port_0_en <= en;
    sig_bramR_port_0_we <= we;
    sig_bramR_port_1_addr <= addr;
    sig_bramR_port_1_clk <= clk;
    sig_bramR_port_1_din <= in_r_b;
    sig_bramR_port_1_en <= en;
    sig_bramR_port_1_we <= we;
    sig_bramW_port_0_addr <= addr;
    sig_bramW_port_0_clk <= clk;
    sig_bramW_port_0_din <= in_w_a;
    sig_bramW_port_0_en <= en;
    sig_bramW_port_0_we <= we;
    sig_bramW_port_1_addr <= addr;
    sig_bramW_port_1_clk <= clk;
    sig_bramW_port_1_din <= in_w_b;
    sig_bramW_port_1_en <= en;
    sig_bramW_port_1_we <= we;
    ASSERT ADDR_WIDTH = 8 REPORT "Generated only for this value" SEVERITY error;
    ASSERT DATA_WIDTH = 64 REPORT "Generated only for this value" SEVERITY error;
END ARCHITECTURE;
