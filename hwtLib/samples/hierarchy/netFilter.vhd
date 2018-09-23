library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY hfe IS
    GENERIC (din_DATA_WIDTH: INTEGER := 64;
        din_IS_BIGENDIAN: BOOLEAN := False;
        dout_DATA_WIDTH: INTEGER := 64;
        dout_IS_BIGENDIAN: BOOLEAN := False;
        headers_DATA_WIDTH: INTEGER := 64;
        headers_IS_BIGENDIAN: BOOLEAN := False
    );
    PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
        din_last: IN STD_LOGIC;
        din_ready: OUT STD_LOGIC;
        din_strb: IN STD_LOGIC_VECTOR((din_DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid: IN STD_LOGIC;
        dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
        dout_last: OUT STD_LOGIC;
        dout_ready: IN STD_LOGIC;
        dout_strb: OUT STD_LOGIC_VECTOR((dout_DATA_WIDTH / 8) - 1 DOWNTO 0);
        dout_valid: OUT STD_LOGIC;
        headers_data: OUT STD_LOGIC_VECTOR(headers_DATA_WIDTH - 1 DOWNTO 0);
        headers_last: OUT STD_LOGIC;
        headers_ready: IN STD_LOGIC;
        headers_strb: OUT STD_LOGIC_VECTOR((headers_DATA_WIDTH / 8) - 1 DOWNTO 0);
        headers_valid: OUT STD_LOGIC
    );
END hfe;

ARCHITECTURE rtl OF hfe IS
BEGIN
    din_ready <= 'X';
    dout_data <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
    dout_last <= 'X';
    dout_strb <= "XXXXXXXX";
    dout_valid <= 'X';
    headers_data <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
    headers_last <= 'X';
    headers_strb <= "XXXXXXXX";
    headers_valid <= 'X';
END ARCHITECTURE rtl;
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY patternMatch IS
    GENERIC (din_DATA_WIDTH: INTEGER := 64;
        din_IS_BIGENDIAN: BOOLEAN := False;
        match_DATA_WIDTH: INTEGER := 64;
        match_IS_BIGENDIAN: BOOLEAN := False
    );
    PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
        din_last: IN STD_LOGIC;
        din_ready: OUT STD_LOGIC;
        din_strb: IN STD_LOGIC_VECTOR((din_DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid: IN STD_LOGIC;
        match_data: OUT STD_LOGIC_VECTOR(match_DATA_WIDTH - 1 DOWNTO 0);
        match_last: OUT STD_LOGIC;
        match_ready: IN STD_LOGIC;
        match_strb: OUT STD_LOGIC_VECTOR((match_DATA_WIDTH / 8) - 1 DOWNTO 0);
        match_valid: OUT STD_LOGIC
    );
END patternMatch;

ARCHITECTURE rtl OF patternMatch IS
BEGIN
    din_ready <= 'X';
    match_data <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
    match_last <= 'X';
    match_strb <= "XXXXXXXX";
    match_valid <= 'X';
END ARCHITECTURE rtl;
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY filter IS
    GENERIC (cfg_ADDR_WIDTH: INTEGER := 32;
        cfg_DATA_WIDTH: INTEGER := 64;
        din_DATA_WIDTH: INTEGER := 64;
        din_IS_BIGENDIAN: BOOLEAN := False;
        dout_DATA_WIDTH: INTEGER := 64;
        dout_IS_BIGENDIAN: BOOLEAN := False;
        headers_DATA_WIDTH: INTEGER := 64;
        headers_IS_BIGENDIAN: BOOLEAN := False;
        patternMatch_DATA_WIDTH: INTEGER := 64;
        patternMatch_IS_BIGENDIAN: BOOLEAN := False
    );
    PORT (cfg_ar_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
        cfg_ar_prot: IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        cfg_ar_ready: OUT STD_LOGIC;
        cfg_ar_valid: IN STD_LOGIC;
        cfg_aw_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
        cfg_aw_prot: IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        cfg_aw_ready: OUT STD_LOGIC;
        cfg_aw_valid: IN STD_LOGIC;
        cfg_b_ready: IN STD_LOGIC;
        cfg_b_resp: OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        cfg_b_valid: OUT STD_LOGIC;
        cfg_r_data: OUT STD_LOGIC_VECTOR(cfg_DATA_WIDTH - 1 DOWNTO 0);
        cfg_r_ready: IN STD_LOGIC;
        cfg_r_resp: OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        cfg_r_valid: OUT STD_LOGIC;
        cfg_w_data: IN STD_LOGIC_VECTOR(cfg_DATA_WIDTH - 1 DOWNTO 0);
        cfg_w_ready: OUT STD_LOGIC;
        cfg_w_strb: IN STD_LOGIC_VECTOR((cfg_DATA_WIDTH / 8) - 1 DOWNTO 0);
        cfg_w_valid: IN STD_LOGIC;
        din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
        din_last: IN STD_LOGIC;
        din_ready: OUT STD_LOGIC;
        din_strb: IN STD_LOGIC_VECTOR((din_DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid: IN STD_LOGIC;
        dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
        dout_last: OUT STD_LOGIC;
        dout_ready: IN STD_LOGIC;
        dout_strb: OUT STD_LOGIC_VECTOR((dout_DATA_WIDTH / 8) - 1 DOWNTO 0);
        dout_valid: OUT STD_LOGIC;
        headers_data: IN STD_LOGIC_VECTOR(headers_DATA_WIDTH - 1 DOWNTO 0);
        headers_last: IN STD_LOGIC;
        headers_ready: OUT STD_LOGIC;
        headers_strb: IN STD_LOGIC_VECTOR((headers_DATA_WIDTH / 8) - 1 DOWNTO 0);
        headers_valid: IN STD_LOGIC;
        patternMatch_data: IN STD_LOGIC_VECTOR(patternMatch_DATA_WIDTH - 1 DOWNTO 0);
        patternMatch_last: IN STD_LOGIC;
        patternMatch_ready: OUT STD_LOGIC;
        patternMatch_strb: IN STD_LOGIC_VECTOR((patternMatch_DATA_WIDTH / 8) - 1 DOWNTO 0);
        patternMatch_valid: IN STD_LOGIC
    );
END filter;

ARCHITECTURE rtl OF filter IS
BEGIN
    cfg_ar_ready <= 'X';
    cfg_aw_ready <= 'X';
    cfg_b_resp <= "XX";
    cfg_b_valid <= 'X';
    cfg_r_data <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
    cfg_r_resp <= "XX";
    cfg_r_valid <= 'X';
    cfg_w_ready <= 'X';
    din_ready <= 'X';
    dout_data <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
    dout_last <= 'X';
    dout_strb <= "XXXXXXXX";
    dout_valid <= 'X';
    headers_ready <= 'X';
    patternMatch_ready <= 'X';
END ARCHITECTURE rtl;
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY exporter IS
    GENERIC (din_DATA_WIDTH: INTEGER := 64;
        din_IS_BIGENDIAN: BOOLEAN := False;
        dout_DATA_WIDTH: INTEGER := 64;
        dout_IS_BIGENDIAN: BOOLEAN := False
    );
    PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
        din_last: IN STD_LOGIC;
        din_ready: OUT STD_LOGIC;
        din_strb: IN STD_LOGIC_VECTOR((din_DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid: IN STD_LOGIC;
        dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
        dout_last: OUT STD_LOGIC;
        dout_ready: IN STD_LOGIC;
        dout_strb: OUT STD_LOGIC_VECTOR((dout_DATA_WIDTH / 8) - 1 DOWNTO 0);
        dout_valid: OUT STD_LOGIC
    );
END exporter;

ARCHITECTURE rtl OF exporter IS
BEGIN
    din_ready <= 'X';
    dout_data <= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
    dout_last <= 'X';
    dout_strb <= "XXXXXXXX";
    dout_valid <= 'X';
END ARCHITECTURE rtl;
--
--    Stream duplicator for AxiStream interfaces
--    
--    :see: :class:`hwtLib.handshaked.splitCopy.HsSplitCopy`
--
--    .. hwt-schematic:: _example_AxiSSplitCopy
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY gen_dout_splitCopy_0 IS
    GENERIC (DATA_WIDTH: INTEGER := 64;
        IS_BIGENDIAN: BOOLEAN := False;
        OUTPUTS: INTEGER := 2
    );
    PORT (dataIn_data: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        dataIn_last: IN STD_LOGIC;
        dataIn_ready: OUT STD_LOGIC;
        dataIn_strb: IN STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        dataIn_valid: IN STD_LOGIC;
        dataOut_0_data: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        dataOut_0_last: OUT STD_LOGIC;
        dataOut_0_ready: IN STD_LOGIC;
        dataOut_0_strb: OUT STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        dataOut_0_valid: OUT STD_LOGIC;
        dataOut_1_data: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        dataOut_1_last: OUT STD_LOGIC;
        dataOut_1_ready: IN STD_LOGIC;
        dataOut_1_strb: OUT STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        dataOut_1_valid: OUT STD_LOGIC
    );
END gen_dout_splitCopy_0;

ARCHITECTURE rtl OF gen_dout_splitCopy_0 IS
BEGIN
    dataIn_ready <= dataOut_0_ready AND dataOut_1_ready;
    dataOut_0_data <= dataIn_data;
    dataOut_0_last <= dataIn_last;
    dataOut_0_strb <= dataIn_strb;
    dataOut_0_valid <= dataIn_valid AND dataOut_1_ready;
    dataOut_1_data <= dataIn_data;
    dataOut_1_last <= dataIn_last;
    dataOut_1_strb <= dataIn_strb;
    dataOut_1_valid <= dataIn_valid AND dataOut_0_ready;
END ARCHITECTURE rtl;
--
--    This unit has actually no functionality it is just example
--    of hierarchical design.
--    
--    .. hwt-schematic::
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY NetFilter IS
    GENERIC (DATA_WIDTH: INTEGER := 64;
        cfg_ADDR_WIDTH: INTEGER := 32;
        din_IS_BIGENDIAN: BOOLEAN := False;
        export_IS_BIGENDIAN: BOOLEAN := False
    );
    PORT (cfg_ar_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
        cfg_ar_prot: IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        cfg_ar_ready: OUT STD_LOGIC;
        cfg_ar_valid: IN STD_LOGIC;
        cfg_aw_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
        cfg_aw_prot: IN STD_LOGIC_VECTOR(2 DOWNTO 0);
        cfg_aw_ready: OUT STD_LOGIC;
        cfg_aw_valid: IN STD_LOGIC;
        cfg_b_ready: IN STD_LOGIC;
        cfg_b_resp: OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        cfg_b_valid: OUT STD_LOGIC;
        cfg_r_data: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        cfg_r_ready: IN STD_LOGIC;
        cfg_r_resp: OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        cfg_r_valid: OUT STD_LOGIC;
        cfg_w_data: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        cfg_w_ready: OUT STD_LOGIC;
        cfg_w_strb: IN STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        cfg_w_valid: IN STD_LOGIC;
        clk: IN STD_LOGIC;
        din_data: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        din_last: IN STD_LOGIC;
        din_ready: OUT STD_LOGIC;
        din_strb: IN STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid: IN STD_LOGIC;
        export_data: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        export_last: OUT STD_LOGIC;
        export_ready: IN STD_LOGIC;
        export_strb: OUT STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        export_valid: OUT STD_LOGIC;
        rst_n: IN STD_LOGIC
    );
END NetFilter;

ARCHITECTURE rtl OF NetFilter IS
    SIGNAL sig_exporter_din_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_exporter_din_last: STD_LOGIC;
    SIGNAL sig_exporter_din_ready: STD_LOGIC;
    SIGNAL sig_exporter_din_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_exporter_din_valid: STD_LOGIC;
    SIGNAL sig_exporter_dout_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_exporter_dout_last: STD_LOGIC;
    SIGNAL sig_exporter_dout_ready: STD_LOGIC;
    SIGNAL sig_exporter_dout_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_exporter_dout_valid: STD_LOGIC;
    SIGNAL sig_filter_cfg_ar_addr: STD_LOGIC_VECTOR(31 DOWNTO 0);
    SIGNAL sig_filter_cfg_ar_prot: STD_LOGIC_VECTOR(2 DOWNTO 0);
    SIGNAL sig_filter_cfg_ar_ready: STD_LOGIC;
    SIGNAL sig_filter_cfg_ar_valid: STD_LOGIC;
    SIGNAL sig_filter_cfg_aw_addr: STD_LOGIC_VECTOR(31 DOWNTO 0);
    SIGNAL sig_filter_cfg_aw_prot: STD_LOGIC_VECTOR(2 DOWNTO 0);
    SIGNAL sig_filter_cfg_aw_ready: STD_LOGIC;
    SIGNAL sig_filter_cfg_aw_valid: STD_LOGIC;
    SIGNAL sig_filter_cfg_b_ready: STD_LOGIC;
    SIGNAL sig_filter_cfg_b_resp: STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_filter_cfg_b_valid: STD_LOGIC;
    SIGNAL sig_filter_cfg_r_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_cfg_r_ready: STD_LOGIC;
    SIGNAL sig_filter_cfg_r_resp: STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_filter_cfg_r_valid: STD_LOGIC;
    SIGNAL sig_filter_cfg_w_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_cfg_w_ready: STD_LOGIC;
    SIGNAL sig_filter_cfg_w_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_cfg_w_valid: STD_LOGIC;
    SIGNAL sig_filter_din_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_din_last: STD_LOGIC;
    SIGNAL sig_filter_din_ready: STD_LOGIC;
    SIGNAL sig_filter_din_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_din_valid: STD_LOGIC;
    SIGNAL sig_filter_dout_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_dout_last: STD_LOGIC;
    SIGNAL sig_filter_dout_ready: STD_LOGIC;
    SIGNAL sig_filter_dout_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_dout_valid: STD_LOGIC;
    SIGNAL sig_filter_headers_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_headers_last: STD_LOGIC;
    SIGNAL sig_filter_headers_ready: STD_LOGIC;
    SIGNAL sig_filter_headers_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_headers_valid: STD_LOGIC;
    SIGNAL sig_filter_patternMatch_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_patternMatch_last: STD_LOGIC;
    SIGNAL sig_filter_patternMatch_ready: STD_LOGIC;
    SIGNAL sig_filter_patternMatch_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_patternMatch_valid: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_last: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_ready: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_valid: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_0_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_0_last: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_0_ready: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_0_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_0_valid: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_1_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_1_last: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_1_ready: STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_1_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_1_valid: STD_LOGIC;
    SIGNAL sig_hfe_din_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_hfe_din_last: STD_LOGIC;
    SIGNAL sig_hfe_din_ready: STD_LOGIC;
    SIGNAL sig_hfe_din_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_hfe_din_valid: STD_LOGIC;
    SIGNAL sig_hfe_dout_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_hfe_dout_last: STD_LOGIC;
    SIGNAL sig_hfe_dout_ready: STD_LOGIC;
    SIGNAL sig_hfe_dout_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_hfe_dout_valid: STD_LOGIC;
    SIGNAL sig_hfe_headers_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_hfe_headers_last: STD_LOGIC;
    SIGNAL sig_hfe_headers_ready: STD_LOGIC;
    SIGNAL sig_hfe_headers_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_hfe_headers_valid: STD_LOGIC;
    SIGNAL sig_patternMatch_din_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_patternMatch_din_last: STD_LOGIC;
    SIGNAL sig_patternMatch_din_ready: STD_LOGIC;
    SIGNAL sig_patternMatch_din_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_patternMatch_din_valid: STD_LOGIC;
    SIGNAL sig_patternMatch_match_data: STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_patternMatch_match_last: STD_LOGIC;
    SIGNAL sig_patternMatch_match_ready: STD_LOGIC;
    SIGNAL sig_patternMatch_match_strb: STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_patternMatch_match_valid: STD_LOGIC;
    COMPONENT exporter IS
       GENERIC (din_DATA_WIDTH: INTEGER := 64;
            din_IS_BIGENDIAN: BOOLEAN := False;
            dout_DATA_WIDTH: INTEGER := 64;
            dout_IS_BIGENDIAN: BOOLEAN := False
       );
       PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
            din_last: IN STD_LOGIC;
            din_ready: OUT STD_LOGIC;
            din_strb: IN STD_LOGIC_VECTOR((din_DATA_WIDTH / 8) - 1 DOWNTO 0);
            din_valid: IN STD_LOGIC;
            dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
            dout_last: OUT STD_LOGIC;
            dout_ready: IN STD_LOGIC;
            dout_strb: OUT STD_LOGIC_VECTOR((dout_DATA_WIDTH / 8) - 1 DOWNTO 0);
            dout_valid: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT filter IS
       GENERIC (cfg_ADDR_WIDTH: INTEGER := 32;
            cfg_DATA_WIDTH: INTEGER := 64;
            din_DATA_WIDTH: INTEGER := 64;
            din_IS_BIGENDIAN: BOOLEAN := False;
            dout_DATA_WIDTH: INTEGER := 64;
            dout_IS_BIGENDIAN: BOOLEAN := False;
            headers_DATA_WIDTH: INTEGER := 64;
            headers_IS_BIGENDIAN: BOOLEAN := False;
            patternMatch_DATA_WIDTH: INTEGER := 64;
            patternMatch_IS_BIGENDIAN: BOOLEAN := False
       );
       PORT (cfg_ar_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
            cfg_ar_prot: IN STD_LOGIC_VECTOR(2 DOWNTO 0);
            cfg_ar_ready: OUT STD_LOGIC;
            cfg_ar_valid: IN STD_LOGIC;
            cfg_aw_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
            cfg_aw_prot: IN STD_LOGIC_VECTOR(2 DOWNTO 0);
            cfg_aw_ready: OUT STD_LOGIC;
            cfg_aw_valid: IN STD_LOGIC;
            cfg_b_ready: IN STD_LOGIC;
            cfg_b_resp: OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
            cfg_b_valid: OUT STD_LOGIC;
            cfg_r_data: OUT STD_LOGIC_VECTOR(cfg_DATA_WIDTH - 1 DOWNTO 0);
            cfg_r_ready: IN STD_LOGIC;
            cfg_r_resp: OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
            cfg_r_valid: OUT STD_LOGIC;
            cfg_w_data: IN STD_LOGIC_VECTOR(cfg_DATA_WIDTH - 1 DOWNTO 0);
            cfg_w_ready: OUT STD_LOGIC;
            cfg_w_strb: IN STD_LOGIC_VECTOR((cfg_DATA_WIDTH / 8) - 1 DOWNTO 0);
            cfg_w_valid: IN STD_LOGIC;
            din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
            din_last: IN STD_LOGIC;
            din_ready: OUT STD_LOGIC;
            din_strb: IN STD_LOGIC_VECTOR((din_DATA_WIDTH / 8) - 1 DOWNTO 0);
            din_valid: IN STD_LOGIC;
            dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
            dout_last: OUT STD_LOGIC;
            dout_ready: IN STD_LOGIC;
            dout_strb: OUT STD_LOGIC_VECTOR((dout_DATA_WIDTH / 8) - 1 DOWNTO 0);
            dout_valid: OUT STD_LOGIC;
            headers_data: IN STD_LOGIC_VECTOR(headers_DATA_WIDTH - 1 DOWNTO 0);
            headers_last: IN STD_LOGIC;
            headers_ready: OUT STD_LOGIC;
            headers_strb: IN STD_LOGIC_VECTOR((headers_DATA_WIDTH / 8) - 1 DOWNTO 0);
            headers_valid: IN STD_LOGIC;
            patternMatch_data: IN STD_LOGIC_VECTOR(patternMatch_DATA_WIDTH - 1 DOWNTO 0);
            patternMatch_last: IN STD_LOGIC;
            patternMatch_ready: OUT STD_LOGIC;
            patternMatch_strb: IN STD_LOGIC_VECTOR((patternMatch_DATA_WIDTH / 8) - 1 DOWNTO 0);
            patternMatch_valid: IN STD_LOGIC
       );
    END COMPONENT;

    COMPONENT gen_dout_splitCopy_0 IS
       GENERIC (DATA_WIDTH: INTEGER := 64;
            IS_BIGENDIAN: BOOLEAN := False;
            OUTPUTS: INTEGER := 2
       );
       PORT (dataIn_data: IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
            dataIn_last: IN STD_LOGIC;
            dataIn_ready: OUT STD_LOGIC;
            dataIn_strb: IN STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
            dataIn_valid: IN STD_LOGIC;
            dataOut_0_data: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
            dataOut_0_last: OUT STD_LOGIC;
            dataOut_0_ready: IN STD_LOGIC;
            dataOut_0_strb: OUT STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
            dataOut_0_valid: OUT STD_LOGIC;
            dataOut_1_data: OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
            dataOut_1_last: OUT STD_LOGIC;
            dataOut_1_ready: IN STD_LOGIC;
            dataOut_1_strb: OUT STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
            dataOut_1_valid: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT hfe IS
       GENERIC (din_DATA_WIDTH: INTEGER := 64;
            din_IS_BIGENDIAN: BOOLEAN := False;
            dout_DATA_WIDTH: INTEGER := 64;
            dout_IS_BIGENDIAN: BOOLEAN := False;
            headers_DATA_WIDTH: INTEGER := 64;
            headers_IS_BIGENDIAN: BOOLEAN := False
       );
       PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
            din_last: IN STD_LOGIC;
            din_ready: OUT STD_LOGIC;
            din_strb: IN STD_LOGIC_VECTOR((din_DATA_WIDTH / 8) - 1 DOWNTO 0);
            din_valid: IN STD_LOGIC;
            dout_data: OUT STD_LOGIC_VECTOR(dout_DATA_WIDTH - 1 DOWNTO 0);
            dout_last: OUT STD_LOGIC;
            dout_ready: IN STD_LOGIC;
            dout_strb: OUT STD_LOGIC_VECTOR((dout_DATA_WIDTH / 8) - 1 DOWNTO 0);
            dout_valid: OUT STD_LOGIC;
            headers_data: OUT STD_LOGIC_VECTOR(headers_DATA_WIDTH - 1 DOWNTO 0);
            headers_last: OUT STD_LOGIC;
            headers_ready: IN STD_LOGIC;
            headers_strb: OUT STD_LOGIC_VECTOR((headers_DATA_WIDTH / 8) - 1 DOWNTO 0);
            headers_valid: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT patternMatch IS
       GENERIC (din_DATA_WIDTH: INTEGER := 64;
            din_IS_BIGENDIAN: BOOLEAN := False;
            match_DATA_WIDTH: INTEGER := 64;
            match_IS_BIGENDIAN: BOOLEAN := False
       );
       PORT (din_data: IN STD_LOGIC_VECTOR(din_DATA_WIDTH - 1 DOWNTO 0);
            din_last: IN STD_LOGIC;
            din_ready: OUT STD_LOGIC;
            din_strb: IN STD_LOGIC_VECTOR((din_DATA_WIDTH / 8) - 1 DOWNTO 0);
            din_valid: IN STD_LOGIC;
            match_data: OUT STD_LOGIC_VECTOR(match_DATA_WIDTH - 1 DOWNTO 0);
            match_last: OUT STD_LOGIC;
            match_ready: IN STD_LOGIC;
            match_strb: OUT STD_LOGIC_VECTOR((match_DATA_WIDTH / 8) - 1 DOWNTO 0);
            match_valid: OUT STD_LOGIC
       );
    END COMPONENT;

BEGIN
    exporter_inst: COMPONENT exporter
        GENERIC MAP (din_DATA_WIDTH => 64,
            din_IS_BIGENDIAN => False,
            dout_DATA_WIDTH => 64,
            dout_IS_BIGENDIAN => False
        )
        PORT MAP (din_data => sig_exporter_din_data,
            din_last => sig_exporter_din_last,
            din_ready => sig_exporter_din_ready,
            din_strb => sig_exporter_din_strb,
            din_valid => sig_exporter_din_valid,
            dout_data => sig_exporter_dout_data,
            dout_last => sig_exporter_dout_last,
            dout_ready => sig_exporter_dout_ready,
            dout_strb => sig_exporter_dout_strb,
            dout_valid => sig_exporter_dout_valid
        );

    filter_inst: COMPONENT filter
        GENERIC MAP (cfg_ADDR_WIDTH => 32,
            cfg_DATA_WIDTH => 64,
            din_DATA_WIDTH => 64,
            din_IS_BIGENDIAN => False,
            dout_DATA_WIDTH => 64,
            dout_IS_BIGENDIAN => False,
            headers_DATA_WIDTH => 64,
            headers_IS_BIGENDIAN => False,
            patternMatch_DATA_WIDTH => 64,
            patternMatch_IS_BIGENDIAN => False
        )
        PORT MAP (cfg_ar_addr => sig_filter_cfg_ar_addr,
            cfg_ar_prot => sig_filter_cfg_ar_prot,
            cfg_ar_ready => sig_filter_cfg_ar_ready,
            cfg_ar_valid => sig_filter_cfg_ar_valid,
            cfg_aw_addr => sig_filter_cfg_aw_addr,
            cfg_aw_prot => sig_filter_cfg_aw_prot,
            cfg_aw_ready => sig_filter_cfg_aw_ready,
            cfg_aw_valid => sig_filter_cfg_aw_valid,
            cfg_b_ready => sig_filter_cfg_b_ready,
            cfg_b_resp => sig_filter_cfg_b_resp,
            cfg_b_valid => sig_filter_cfg_b_valid,
            cfg_r_data => sig_filter_cfg_r_data,
            cfg_r_ready => sig_filter_cfg_r_ready,
            cfg_r_resp => sig_filter_cfg_r_resp,
            cfg_r_valid => sig_filter_cfg_r_valid,
            cfg_w_data => sig_filter_cfg_w_data,
            cfg_w_ready => sig_filter_cfg_w_ready,
            cfg_w_strb => sig_filter_cfg_w_strb,
            cfg_w_valid => sig_filter_cfg_w_valid,
            din_data => sig_filter_din_data,
            din_last => sig_filter_din_last,
            din_ready => sig_filter_din_ready,
            din_strb => sig_filter_din_strb,
            din_valid => sig_filter_din_valid,
            dout_data => sig_filter_dout_data,
            dout_last => sig_filter_dout_last,
            dout_ready => sig_filter_dout_ready,
            dout_strb => sig_filter_dout_strb,
            dout_valid => sig_filter_dout_valid,
            headers_data => sig_filter_headers_data,
            headers_last => sig_filter_headers_last,
            headers_ready => sig_filter_headers_ready,
            headers_strb => sig_filter_headers_strb,
            headers_valid => sig_filter_headers_valid,
            patternMatch_data => sig_filter_patternMatch_data,
            patternMatch_last => sig_filter_patternMatch_last,
            patternMatch_ready => sig_filter_patternMatch_ready,
            patternMatch_strb => sig_filter_patternMatch_strb,
            patternMatch_valid => sig_filter_patternMatch_valid
        );

    gen_dout_splitCopy_0_inst: COMPONENT gen_dout_splitCopy_0
        GENERIC MAP (DATA_WIDTH => 64,
            IS_BIGENDIAN => False,
            OUTPUTS => 2
        )
        PORT MAP (dataIn_data => sig_gen_dout_splitCopy_0_dataIn_data,
            dataIn_last => sig_gen_dout_splitCopy_0_dataIn_last,
            dataIn_ready => sig_gen_dout_splitCopy_0_dataIn_ready,
            dataIn_strb => sig_gen_dout_splitCopy_0_dataIn_strb,
            dataIn_valid => sig_gen_dout_splitCopy_0_dataIn_valid,
            dataOut_0_data => sig_gen_dout_splitCopy_0_dataOut_0_data,
            dataOut_0_last => sig_gen_dout_splitCopy_0_dataOut_0_last,
            dataOut_0_ready => sig_gen_dout_splitCopy_0_dataOut_0_ready,
            dataOut_0_strb => sig_gen_dout_splitCopy_0_dataOut_0_strb,
            dataOut_0_valid => sig_gen_dout_splitCopy_0_dataOut_0_valid,
            dataOut_1_data => sig_gen_dout_splitCopy_0_dataOut_1_data,
            dataOut_1_last => sig_gen_dout_splitCopy_0_dataOut_1_last,
            dataOut_1_ready => sig_gen_dout_splitCopy_0_dataOut_1_ready,
            dataOut_1_strb => sig_gen_dout_splitCopy_0_dataOut_1_strb,
            dataOut_1_valid => sig_gen_dout_splitCopy_0_dataOut_1_valid
        );

    hfe_inst: COMPONENT hfe
        GENERIC MAP (din_DATA_WIDTH => 64,
            din_IS_BIGENDIAN => False,
            dout_DATA_WIDTH => 64,
            dout_IS_BIGENDIAN => False,
            headers_DATA_WIDTH => 64,
            headers_IS_BIGENDIAN => False
        )
        PORT MAP (din_data => sig_hfe_din_data,
            din_last => sig_hfe_din_last,
            din_ready => sig_hfe_din_ready,
            din_strb => sig_hfe_din_strb,
            din_valid => sig_hfe_din_valid,
            dout_data => sig_hfe_dout_data,
            dout_last => sig_hfe_dout_last,
            dout_ready => sig_hfe_dout_ready,
            dout_strb => sig_hfe_dout_strb,
            dout_valid => sig_hfe_dout_valid,
            headers_data => sig_hfe_headers_data,
            headers_last => sig_hfe_headers_last,
            headers_ready => sig_hfe_headers_ready,
            headers_strb => sig_hfe_headers_strb,
            headers_valid => sig_hfe_headers_valid
        );

    patternMatch_inst: COMPONENT patternMatch
        GENERIC MAP (din_DATA_WIDTH => 64,
            din_IS_BIGENDIAN => False,
            match_DATA_WIDTH => 64,
            match_IS_BIGENDIAN => False
        )
        PORT MAP (din_data => sig_patternMatch_din_data,
            din_last => sig_patternMatch_din_last,
            din_ready => sig_patternMatch_din_ready,
            din_strb => sig_patternMatch_din_strb,
            din_valid => sig_patternMatch_din_valid,
            match_data => sig_patternMatch_match_data,
            match_last => sig_patternMatch_match_last,
            match_ready => sig_patternMatch_match_ready,
            match_strb => sig_patternMatch_match_strb,
            match_valid => sig_patternMatch_match_valid
        );

    cfg_ar_ready <= sig_filter_cfg_ar_ready;
    cfg_aw_ready <= sig_filter_cfg_aw_ready;
    cfg_b_resp <= sig_filter_cfg_b_resp;
    cfg_b_valid <= sig_filter_cfg_b_valid;
    cfg_r_data <= sig_filter_cfg_r_data;
    cfg_r_resp <= sig_filter_cfg_r_resp;
    cfg_r_valid <= sig_filter_cfg_r_valid;
    cfg_w_ready <= sig_filter_cfg_w_ready;
    din_ready <= sig_hfe_din_ready;
    export_data <= sig_exporter_dout_data;
    export_last <= sig_exporter_dout_last;
    export_strb <= sig_exporter_dout_strb;
    export_valid <= sig_exporter_dout_valid;
    sig_exporter_din_data <= sig_filter_dout_data;
    sig_exporter_din_last <= sig_filter_dout_last;
    sig_exporter_din_strb <= sig_filter_dout_strb;
    sig_exporter_din_valid <= sig_filter_dout_valid;
    sig_exporter_dout_ready <= export_ready;
    sig_filter_cfg_ar_addr <= cfg_ar_addr;
    sig_filter_cfg_ar_prot <= cfg_ar_prot;
    sig_filter_cfg_ar_valid <= cfg_ar_valid;
    sig_filter_cfg_aw_addr <= cfg_aw_addr;
    sig_filter_cfg_aw_prot <= cfg_aw_prot;
    sig_filter_cfg_aw_valid <= cfg_aw_valid;
    sig_filter_cfg_b_ready <= cfg_b_ready;
    sig_filter_cfg_r_ready <= cfg_r_ready;
    sig_filter_cfg_w_data <= cfg_w_data;
    sig_filter_cfg_w_strb <= cfg_w_strb;
    sig_filter_cfg_w_valid <= cfg_w_valid;
    sig_filter_din_data <= sig_gen_dout_splitCopy_0_dataOut_1_data;
    sig_filter_din_last <= sig_gen_dout_splitCopy_0_dataOut_1_last;
    sig_filter_din_strb <= sig_gen_dout_splitCopy_0_dataOut_1_strb;
    sig_filter_din_valid <= sig_gen_dout_splitCopy_0_dataOut_1_valid;
    sig_filter_dout_ready <= sig_exporter_din_ready;
    sig_filter_headers_data <= sig_hfe_headers_data;
    sig_filter_headers_last <= sig_hfe_headers_last;
    sig_filter_headers_strb <= sig_hfe_headers_strb;
    sig_filter_headers_valid <= sig_hfe_headers_valid;
    sig_filter_patternMatch_data <= sig_patternMatch_match_data;
    sig_filter_patternMatch_last <= sig_patternMatch_match_last;
    sig_filter_patternMatch_strb <= sig_patternMatch_match_strb;
    sig_filter_patternMatch_valid <= sig_patternMatch_match_valid;
    sig_gen_dout_splitCopy_0_dataIn_data <= sig_hfe_dout_data;
    sig_gen_dout_splitCopy_0_dataIn_last <= sig_hfe_dout_last;
    sig_gen_dout_splitCopy_0_dataIn_strb <= sig_hfe_dout_strb;
    sig_gen_dout_splitCopy_0_dataIn_valid <= sig_hfe_dout_valid;
    sig_gen_dout_splitCopy_0_dataOut_0_ready <= sig_patternMatch_din_ready;
    sig_gen_dout_splitCopy_0_dataOut_1_ready <= sig_filter_din_ready;
    sig_hfe_din_data <= din_data;
    sig_hfe_din_last <= din_last;
    sig_hfe_din_strb <= din_strb;
    sig_hfe_din_valid <= din_valid;
    sig_hfe_dout_ready <= sig_gen_dout_splitCopy_0_dataIn_ready;
    sig_hfe_headers_ready <= sig_filter_headers_ready;
    sig_patternMatch_din_data <= sig_gen_dout_splitCopy_0_dataOut_0_data;
    sig_patternMatch_din_last <= sig_gen_dout_splitCopy_0_dataOut_0_last;
    sig_patternMatch_din_strb <= sig_gen_dout_splitCopy_0_dataOut_0_strb;
    sig_patternMatch_din_valid <= sig_gen_dout_splitCopy_0_dataOut_0_valid;
    sig_patternMatch_match_ready <= sig_filter_patternMatch_ready;
END ARCHITECTURE rtl;