LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    True dual port RAM.
--    :note: write-first variant 
--
--    .. hwt-schematic::
--    
ENTITY Ram_dp IS
    GENERIC(
        ADDR_WIDTH : INTEGER := 8;
        DATA_WIDTH : INTEGER := 64
    );
    PORT(
        a_addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        a_clk : IN STD_LOGIC;
        a_din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        a_dout : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        a_en : IN STD_LOGIC;
        a_we : IN STD_LOGIC;
        b_addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        b_clk : IN STD_LOGIC;
        b_din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_dout : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_en : IN STD_LOGIC;
        b_we : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF Ram_dp IS
    TYPE arr_t_0 IS ARRAY (255 DOWNTO 0) OF STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL ram_memory : arr_t_0;
BEGIN
    assig_process_a_dout: PROCESS(a_clk)
    BEGIN
        IF RISING_EDGE(a_clk) AND a_en = '1' THEN
            IF a_we = '1' THEN
                ram_memory(TO_INTEGER(UNSIGNED(a_addr))) <= a_din;
            END IF;
            a_dout <= ram_memory(TO_INTEGER(UNSIGNED(a_addr)));
        END IF;
    END PROCESS;
    assig_process_b_dout: PROCESS(b_clk)
    BEGIN
        IF RISING_EDGE(b_clk) AND b_en = '1' THEN
            IF b_we = '1' THEN
                ram_memory(TO_INTEGER(UNSIGNED(b_addr))) <= b_din;
            END IF;
            b_dout <= ram_memory(TO_INTEGER(UNSIGNED(b_addr)));
        END IF;
    END PROCESS;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    .. hwt-schematic::
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
    --    True dual port RAM.
    --    :note: write-first variant 
    --
    --    .. hwt-schematic::
    --    
    COMPONENT Ram_dp IS
        GENERIC(
            ADDR_WIDTH : INTEGER := 8;
            DATA_WIDTH : INTEGER := 64
        );
        PORT(
            a_addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            a_clk : IN STD_LOGIC;
            a_din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
            a_dout : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
            a_en : IN STD_LOGIC;
            a_we : IN STD_LOGIC;
            b_addr : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            b_clk : IN STD_LOGIC;
            b_din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
            b_dout : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
            b_en : IN STD_LOGIC;
            b_we : IN STD_LOGIC
        );
    END COMPONENT;
    SIGNAL sig_bramR_a_addr : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramR_a_clk : STD_LOGIC;
    SIGNAL sig_bramR_a_din : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_a_dout : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_a_en : STD_LOGIC;
    SIGNAL sig_bramR_a_we : STD_LOGIC;
    SIGNAL sig_bramR_b_addr : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramR_b_clk : STD_LOGIC;
    SIGNAL sig_bramR_b_din : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_b_dout : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramR_b_en : STD_LOGIC;
    SIGNAL sig_bramR_b_we : STD_LOGIC;
    SIGNAL sig_bramW_a_addr : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramW_a_clk : STD_LOGIC;
    SIGNAL sig_bramW_a_din : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_a_dout : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_a_en : STD_LOGIC;
    SIGNAL sig_bramW_a_we : STD_LOGIC;
    SIGNAL sig_bramW_b_addr : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_bramW_b_clk : STD_LOGIC;
    SIGNAL sig_bramW_b_din : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_b_dout : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_bramW_b_en : STD_LOGIC;
    SIGNAL sig_bramW_b_we : STD_LOGIC;
BEGIN
    bramR_inst: Ram_dp GENERIC MAP(
        ADDR_WIDTH => 8,
        DATA_WIDTH => 64
    ) PORT MAP(
        a_addr => sig_bramR_a_addr,
        a_clk => sig_bramR_a_clk,
        a_din => sig_bramR_a_din,
        a_dout => sig_bramR_a_dout,
        a_en => sig_bramR_a_en,
        a_we => sig_bramR_a_we,
        b_addr => sig_bramR_b_addr,
        b_clk => sig_bramR_b_clk,
        b_din => sig_bramR_b_din,
        b_dout => sig_bramR_b_dout,
        b_en => sig_bramR_b_en,
        b_we => sig_bramR_b_we
    );
    bramW_inst: Ram_dp GENERIC MAP(
        ADDR_WIDTH => 8,
        DATA_WIDTH => 64
    ) PORT MAP(
        a_addr => sig_bramW_a_addr,
        a_clk => sig_bramW_a_clk,
        a_din => sig_bramW_a_din,
        a_dout => sig_bramW_a_dout,
        a_en => sig_bramW_a_en,
        a_we => sig_bramW_a_we,
        b_addr => sig_bramW_b_addr,
        b_clk => sig_bramW_b_clk,
        b_din => sig_bramW_b_din,
        b_dout => sig_bramW_b_dout,
        b_en => sig_bramW_b_en,
        b_we => sig_bramW_b_we
    );
    out_r_a <= sig_bramR_a_dout;
    out_r_b <= sig_bramR_b_dout;
    out_w_a <= sig_bramW_a_dout;
    out_w_b <= sig_bramW_b_dout;
    sig_bramR_a_addr <= addr;
    sig_bramR_a_clk <= clk;
    sig_bramR_a_din <= in_r_a;
    sig_bramR_a_en <= en;
    sig_bramR_a_we <= we;
    sig_bramR_b_addr <= addr;
    sig_bramR_b_clk <= clk;
    sig_bramR_b_din <= in_r_b;
    sig_bramR_b_en <= en;
    sig_bramR_b_we <= we;
    sig_bramW_a_addr <= addr;
    sig_bramW_a_clk <= clk;
    sig_bramW_a_din <= in_w_a;
    sig_bramW_a_en <= en;
    sig_bramW_a_we <= we;
    sig_bramW_b_addr <= addr;
    sig_bramW_b_clk <= clk;
    sig_bramW_b_din <= in_w_b;
    sig_bramW_b_en <= en;
    sig_bramW_b_we <= we;
END ARCHITECTURE;
