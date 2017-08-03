netFilter_vhdl = \
"""library IEEE;
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
        cfg_ar_ready: OUT STD_LOGIC;
        cfg_ar_valid: IN STD_LOGIC;
        cfg_aw_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
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
        dataOut_data: OUT STD_LOGIC_VECTOR((DATA_WIDTH * OUTPUTS) - 1 DOWNTO 0);
        dataOut_last: OUT STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0);
        dataOut_ready: IN STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0);
        dataOut_strb: OUT STD_LOGIC_VECTOR(((DATA_WIDTH / 8) * OUTPUTS) - 1 DOWNTO 0);
        dataOut_valid: OUT STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0)
    );
END gen_dout_splitCopy_0;

ARCHITECTURE rtl OF gen_dout_splitCopy_0 IS
BEGIN
    dataIn_ready <= (dataOut_ready(0)) AND (dataOut_ready(1));
    dataOut_data(63 DOWNTO 0) <= dataIn_data;
    dataOut_data(127 DOWNTO 64) <= dataIn_data;
    dataOut_last(0) <= dataIn_last;
    dataOut_last(1) <= dataIn_last;
    dataOut_strb(7 DOWNTO 0) <= dataIn_strb;
    dataOut_strb(15 DOWNTO 8) <= dataIn_strb;
    dataOut_valid(0) <= dataIn_valid AND (dataOut_ready(1));
    dataOut_valid(1) <= dataIn_valid AND (dataOut_ready(0));
END ARCHITECTURE rtl;
--
--    This unit has actually no functionality it is just example of hierarchical design.
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
        cfg_ar_ready: OUT STD_LOGIC;
        cfg_ar_valid: IN STD_LOGIC;
        cfg_aw_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
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
    SIGNAL sig_filter_cfg_ar_ready: STD_LOGIC;
    SIGNAL sig_filter_cfg_ar_valid: STD_LOGIC;
    SIGNAL sig_filter_cfg_aw_addr: STD_LOGIC_VECTOR(31 DOWNTO 0);
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
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_data: STD_LOGIC_VECTOR(127 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_last: STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_ready: STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_strb: STD_LOGIC_VECTOR(15 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_valid: STD_LOGIC_VECTOR(1 DOWNTO 0);
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
            cfg_ar_ready: OUT STD_LOGIC;
            cfg_ar_valid: IN STD_LOGIC;
            cfg_aw_addr: IN STD_LOGIC_VECTOR(cfg_ADDR_WIDTH - 1 DOWNTO 0);
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
            dataOut_data: OUT STD_LOGIC_VECTOR((DATA_WIDTH * OUTPUTS) - 1 DOWNTO 0);
            dataOut_last: OUT STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0);
            dataOut_ready: IN STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0);
            dataOut_strb: OUT STD_LOGIC_VECTOR(((DATA_WIDTH / 8) * OUTPUTS) - 1 DOWNTO 0);
            dataOut_valid: OUT STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0)
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
            cfg_ar_ready => sig_filter_cfg_ar_ready,
            cfg_ar_valid => sig_filter_cfg_ar_valid,
            cfg_aw_addr => sig_filter_cfg_aw_addr,
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
            dataOut_data => sig_gen_dout_splitCopy_0_dataOut_data,
            dataOut_last => sig_gen_dout_splitCopy_0_dataOut_last,
            dataOut_ready => sig_gen_dout_splitCopy_0_dataOut_ready,
            dataOut_strb => sig_gen_dout_splitCopy_0_dataOut_strb,
            dataOut_valid => sig_gen_dout_splitCopy_0_dataOut_valid
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
    sig_filter_cfg_ar_valid <= cfg_ar_valid;
    sig_filter_cfg_aw_addr <= cfg_aw_addr;
    sig_filter_cfg_aw_valid <= cfg_aw_valid;
    sig_filter_cfg_b_ready <= cfg_b_ready;
    sig_filter_cfg_r_ready <= cfg_r_ready;
    sig_filter_cfg_w_data <= cfg_w_data;
    sig_filter_cfg_w_strb <= cfg_w_strb;
    sig_filter_cfg_w_valid <= cfg_w_valid;
    sig_filter_din_data <= sig_gen_dout_splitCopy_0_dataOut_data(127 DOWNTO 64);
    sig_filter_din_last <= sig_gen_dout_splitCopy_0_dataOut_last(1);
    sig_filter_din_strb <= sig_gen_dout_splitCopy_0_dataOut_strb(15 DOWNTO 8);
    sig_filter_din_valid <= sig_gen_dout_splitCopy_0_dataOut_valid(1);
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
    sig_gen_dout_splitCopy_0_dataOut_ready(0) <= sig_patternMatch_din_ready;
    sig_gen_dout_splitCopy_0_dataOut_ready(1) <= sig_filter_din_ready;
    sig_hfe_din_data <= din_data;
    sig_hfe_din_last <= din_last;
    sig_hfe_din_strb <= din_strb;
    sig_hfe_din_valid <= din_valid;
    sig_hfe_dout_ready <= sig_gen_dout_splitCopy_0_dataIn_ready;
    sig_hfe_headers_ready <= sig_filter_headers_ready;
    sig_patternMatch_din_data <= sig_gen_dout_splitCopy_0_dataOut_data(63 DOWNTO 0);
    sig_patternMatch_din_last <= sig_gen_dout_splitCopy_0_dataOut_last(0);
    sig_patternMatch_din_strb <= sig_gen_dout_splitCopy_0_dataOut_strb(7 DOWNTO 0);
    sig_patternMatch_din_valid <= sig_gen_dout_splitCopy_0_dataOut_valid(0);
    sig_patternMatch_match_ready <= sig_filter_patternMatch_ready;
END ARCHITECTURE rtl;"""


netFilter_verilog = """module hfe #(parameter  din_DATA_WIDTH = 64,
        parameter  din_IS_BIGENDIAN = 0,
        parameter  dout_DATA_WIDTH = 64,
        parameter  dout_IS_BIGENDIAN = 0,
        parameter  headers_DATA_WIDTH = 64,
        parameter  headers_IS_BIGENDIAN = 0
    )(input [din_DATA_WIDTH- 1:0] din_data,
        input din_last,
        output din_ready,
        input [din_DATA_WIDTH / 8- 1:0] din_strb,
        input din_valid,
        output [dout_DATA_WIDTH- 1:0] dout_data,
        output dout_last,
        input dout_ready,
        output [dout_DATA_WIDTH / 8- 1:0] dout_strb,
        output dout_valid,
        output [headers_DATA_WIDTH- 1:0] headers_data,
        output headers_last,
        input headers_ready,
        output [headers_DATA_WIDTH / 8- 1:0] headers_strb,
        output headers_valid
    );

    assign din_ready = 1'bx;
    assign dout_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
    assign dout_last = 1'bx;
    assign dout_strb = 8'bxxxxxxxx;
    assign dout_valid = 1'bx;
    assign headers_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
    assign headers_last = 1'bx;
    assign headers_strb = 8'bxxxxxxxx;
    assign headers_valid = 1'bx;
endmodule
module patternMatch #(parameter  din_DATA_WIDTH = 64,
        parameter  din_IS_BIGENDIAN = 0,
        parameter  match_DATA_WIDTH = 64,
        parameter  match_IS_BIGENDIAN = 0
    )(input [din_DATA_WIDTH- 1:0] din_data,
        input din_last,
        output din_ready,
        input [din_DATA_WIDTH / 8- 1:0] din_strb,
        input din_valid,
        output [match_DATA_WIDTH- 1:0] match_data,
        output match_last,
        input match_ready,
        output [match_DATA_WIDTH / 8- 1:0] match_strb,
        output match_valid
    );

    assign din_ready = 1'bx;
    assign match_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
    assign match_last = 1'bx;
    assign match_strb = 8'bxxxxxxxx;
    assign match_valid = 1'bx;
endmodule
module filter #(parameter  cfg_ADDR_WIDTH = 32,
        parameter  cfg_DATA_WIDTH = 64,
        parameter  din_DATA_WIDTH = 64,
        parameter  din_IS_BIGENDIAN = 0,
        parameter  dout_DATA_WIDTH = 64,
        parameter  dout_IS_BIGENDIAN = 0,
        parameter  headers_DATA_WIDTH = 64,
        parameter  headers_IS_BIGENDIAN = 0,
        parameter  patternMatch_DATA_WIDTH = 64,
        parameter  patternMatch_IS_BIGENDIAN = 0
    )(input [cfg_ADDR_WIDTH- 1:0] cfg_ar_addr,
        output cfg_ar_ready,
        input cfg_ar_valid,
        input [cfg_ADDR_WIDTH- 1:0] cfg_aw_addr,
        output cfg_aw_ready,
        input cfg_aw_valid,
        input cfg_b_ready,
        output [1:0] cfg_b_resp,
        output cfg_b_valid,
        output [cfg_DATA_WIDTH- 1:0] cfg_r_data,
        input cfg_r_ready,
        output [1:0] cfg_r_resp,
        output cfg_r_valid,
        input [cfg_DATA_WIDTH- 1:0] cfg_w_data,
        output cfg_w_ready,
        input [cfg_DATA_WIDTH / 8- 1:0] cfg_w_strb,
        input cfg_w_valid,
        input [din_DATA_WIDTH- 1:0] din_data,
        input din_last,
        output din_ready,
        input [din_DATA_WIDTH / 8- 1:0] din_strb,
        input din_valid,
        output [dout_DATA_WIDTH- 1:0] dout_data,
        output dout_last,
        input dout_ready,
        output [dout_DATA_WIDTH / 8- 1:0] dout_strb,
        output dout_valid,
        input [headers_DATA_WIDTH- 1:0] headers_data,
        input headers_last,
        output headers_ready,
        input [headers_DATA_WIDTH / 8- 1:0] headers_strb,
        input headers_valid,
        input [patternMatch_DATA_WIDTH- 1:0] patternMatch_data,
        input patternMatch_last,
        output patternMatch_ready,
        input [patternMatch_DATA_WIDTH / 8- 1:0] patternMatch_strb,
        input patternMatch_valid
    );

    assign cfg_ar_ready = 1'bx;
    assign cfg_aw_ready = 1'bx;
    assign cfg_b_resp = 2'bxx;
    assign cfg_b_valid = 1'bx;
    assign cfg_r_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
    assign cfg_r_resp = 2'bxx;
    assign cfg_r_valid = 1'bx;
    assign cfg_w_ready = 1'bx;
    assign din_ready = 1'bx;
    assign dout_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
    assign dout_last = 1'bx;
    assign dout_strb = 8'bxxxxxxxx;
    assign dout_valid = 1'bx;
    assign headers_ready = 1'bx;
    assign patternMatch_ready = 1'bx;
endmodule
module exporter #(parameter  din_DATA_WIDTH = 64,
        parameter  din_IS_BIGENDIAN = 0,
        parameter  dout_DATA_WIDTH = 64,
        parameter  dout_IS_BIGENDIAN = 0
    )(input [din_DATA_WIDTH- 1:0] din_data,
        input din_last,
        output din_ready,
        input [din_DATA_WIDTH / 8- 1:0] din_strb,
        input din_valid,
        output [dout_DATA_WIDTH- 1:0] dout_data,
        output dout_last,
        input dout_ready,
        output [dout_DATA_WIDTH / 8- 1:0] dout_strb,
        output dout_valid
    );

    assign din_ready = 1'bx;
    assign dout_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
    assign dout_last = 1'bx;
    assign dout_strb = 8'bxxxxxxxx;
    assign dout_valid = 1'bx;
endmodule
module gen_dout_splitCopy_0 #(parameter  DATA_WIDTH = 64,
        parameter  IS_BIGENDIAN = 0,
        parameter  OUTPUTS = 2
    )(input [DATA_WIDTH- 1:0] dataIn_data,
        input dataIn_last,
        output dataIn_ready,
        input [DATA_WIDTH / 8- 1:0] dataIn_strb,
        input dataIn_valid,
        output reg [DATA_WIDTH * OUTPUTS- 1:0] dataOut_data,
        output reg [OUTPUTS- 1:0] dataOut_last,
        input [OUTPUTS- 1:0] dataOut_ready,
        output reg [DATA_WIDTH / 8 * OUTPUTS- 1:0] dataOut_strb,
        output reg [OUTPUTS- 1:0] dataOut_valid
    );

    assign dataIn_ready = (dataOut_ready[0]) & (dataOut_ready[1]);
    always @(dataIn_data) begin: assig_process_dataOut_data
        dataOut_data[63:0] <= dataIn_data;
    end

    always @(dataIn_data) begin: assig_process_dataOut_data_0
        dataOut_data[127:64] <= dataIn_data;
    end

    always @(dataIn_last) begin: assig_process_dataOut_last
        dataOut_last[0] <= dataIn_last;
    end

    always @(dataIn_last) begin: assig_process_dataOut_last_0
        dataOut_last[1] <= dataIn_last;
    end

    always @(dataIn_strb) begin: assig_process_dataOut_strb
        dataOut_strb[7:0] <= dataIn_strb;
    end

    always @(dataIn_strb) begin: assig_process_dataOut_strb_0
        dataOut_strb[15:8] <= dataIn_strb;
    end

    always @(dataIn_valid or dataOut_ready) begin: assig_process_dataOut_valid
        dataOut_valid[0] <= dataIn_valid & (dataOut_ready[1]);
    end

    always @(dataIn_valid or dataOut_ready) begin: assig_process_dataOut_valid_0
        dataOut_valid[1] <= dataIn_valid & (dataOut_ready[0]);
    end

endmodule
/*

    This unit has actually no functionality it is just example of hierarchical design.
    
*/
module NetFilter #(parameter  DATA_WIDTH = 64,
        parameter  cfg_ADDR_WIDTH = 32,
        parameter  din_IS_BIGENDIAN = 0,
        parameter  export_IS_BIGENDIAN = 0
    )(input [cfg_ADDR_WIDTH- 1:0] cfg_ar_addr,
        output cfg_ar_ready,
        input cfg_ar_valid,
        input [cfg_ADDR_WIDTH- 1:0] cfg_aw_addr,
        output cfg_aw_ready,
        input cfg_aw_valid,
        input cfg_b_ready,
        output [1:0] cfg_b_resp,
        output cfg_b_valid,
        output [DATA_WIDTH- 1:0] cfg_r_data,
        input cfg_r_ready,
        output [1:0] cfg_r_resp,
        output cfg_r_valid,
        input [DATA_WIDTH- 1:0] cfg_w_data,
        output cfg_w_ready,
        input [DATA_WIDTH / 8- 1:0] cfg_w_strb,
        input cfg_w_valid,
        input clk,
        input [DATA_WIDTH- 1:0] din_data,
        input din_last,
        output din_ready,
        input [DATA_WIDTH / 8- 1:0] din_strb,
        input din_valid,
        output [DATA_WIDTH- 1:0] export_data,
        output export_last,
        input export_ready,
        output [DATA_WIDTH / 8- 1:0] export_strb,
        output export_valid,
        input rst_n
    );

    wire [63:0] sig_exporter_din_data;
    wire sig_exporter_din_last;
    wire sig_exporter_din_ready;
    wire [7:0] sig_exporter_din_strb;
    wire sig_exporter_din_valid;
    wire [63:0] sig_exporter_dout_data;
    wire sig_exporter_dout_last;
    wire sig_exporter_dout_ready;
    wire [7:0] sig_exporter_dout_strb;
    wire sig_exporter_dout_valid;
    wire [31:0] sig_filter_cfg_ar_addr;
    wire sig_filter_cfg_ar_ready;
    wire sig_filter_cfg_ar_valid;
    wire [31:0] sig_filter_cfg_aw_addr;
    wire sig_filter_cfg_aw_ready;
    wire sig_filter_cfg_aw_valid;
    wire sig_filter_cfg_b_ready;
    wire [1:0] sig_filter_cfg_b_resp;
    wire sig_filter_cfg_b_valid;
    wire [63:0] sig_filter_cfg_r_data;
    wire sig_filter_cfg_r_ready;
    wire [1:0] sig_filter_cfg_r_resp;
    wire sig_filter_cfg_r_valid;
    wire [63:0] sig_filter_cfg_w_data;
    wire sig_filter_cfg_w_ready;
    wire [7:0] sig_filter_cfg_w_strb;
    wire sig_filter_cfg_w_valid;
    wire [63:0] sig_filter_din_data;
    wire sig_filter_din_last;
    wire sig_filter_din_ready;
    wire [7:0] sig_filter_din_strb;
    wire sig_filter_din_valid;
    wire [63:0] sig_filter_dout_data;
    wire sig_filter_dout_last;
    wire sig_filter_dout_ready;
    wire [7:0] sig_filter_dout_strb;
    wire sig_filter_dout_valid;
    wire [63:0] sig_filter_headers_data;
    wire sig_filter_headers_last;
    wire sig_filter_headers_ready;
    wire [7:0] sig_filter_headers_strb;
    wire sig_filter_headers_valid;
    wire [63:0] sig_filter_patternMatch_data;
    wire sig_filter_patternMatch_last;
    wire sig_filter_patternMatch_ready;
    wire [7:0] sig_filter_patternMatch_strb;
    wire sig_filter_patternMatch_valid;
    wire [63:0] sig_gen_dout_splitCopy_0_dataIn_data;
    wire sig_gen_dout_splitCopy_0_dataIn_last;
    wire sig_gen_dout_splitCopy_0_dataIn_ready;
    wire [7:0] sig_gen_dout_splitCopy_0_dataIn_strb;
    wire sig_gen_dout_splitCopy_0_dataIn_valid;
    wire [127:0] sig_gen_dout_splitCopy_0_dataOut_data;
    wire [1:0] sig_gen_dout_splitCopy_0_dataOut_last;
    reg [1:0] sig_gen_dout_splitCopy_0_dataOut_ready;
    wire [15:0] sig_gen_dout_splitCopy_0_dataOut_strb;
    wire [1:0] sig_gen_dout_splitCopy_0_dataOut_valid;
    wire [63:0] sig_hfe_din_data;
    wire sig_hfe_din_last;
    wire sig_hfe_din_ready;
    wire [7:0] sig_hfe_din_strb;
    wire sig_hfe_din_valid;
    wire [63:0] sig_hfe_dout_data;
    wire sig_hfe_dout_last;
    wire sig_hfe_dout_ready;
    wire [7:0] sig_hfe_dout_strb;
    wire sig_hfe_dout_valid;
    wire [63:0] sig_hfe_headers_data;
    wire sig_hfe_headers_last;
    wire sig_hfe_headers_ready;
    wire [7:0] sig_hfe_headers_strb;
    wire sig_hfe_headers_valid;
    wire [63:0] sig_patternMatch_din_data;
    wire sig_patternMatch_din_last;
    wire sig_patternMatch_din_ready;
    wire [7:0] sig_patternMatch_din_strb;
    wire sig_patternMatch_din_valid;
    wire [63:0] sig_patternMatch_match_data;
    wire sig_patternMatch_match_last;
    wire sig_patternMatch_match_ready;
    wire [7:0] sig_patternMatch_match_strb;
    wire sig_patternMatch_match_valid;
    exporter #(.din_DATA_WIDTH(64),
        .din_IS_BIGENDIAN(0),
        .dout_DATA_WIDTH(64),
        .dout_IS_BIGENDIAN(0)
        ) exporter_inst (.din_data(sig_exporter_din_data),
        .din_last(sig_exporter_din_last),
        .din_ready(sig_exporter_din_ready),
        .din_strb(sig_exporter_din_strb),
        .din_valid(sig_exporter_din_valid),
        .dout_data(sig_exporter_dout_data),
        .dout_last(sig_exporter_dout_last),
        .dout_ready(sig_exporter_dout_ready),
        .dout_strb(sig_exporter_dout_strb),
        .dout_valid(sig_exporter_dout_valid)
        );


    filter #(.cfg_ADDR_WIDTH(32),
        .cfg_DATA_WIDTH(64),
        .din_DATA_WIDTH(64),
        .din_IS_BIGENDIAN(0),
        .dout_DATA_WIDTH(64),
        .dout_IS_BIGENDIAN(0),
        .headers_DATA_WIDTH(64),
        .headers_IS_BIGENDIAN(0),
        .patternMatch_DATA_WIDTH(64),
        .patternMatch_IS_BIGENDIAN(0)
        ) filter_inst (.cfg_ar_addr(sig_filter_cfg_ar_addr),
        .cfg_ar_ready(sig_filter_cfg_ar_ready),
        .cfg_ar_valid(sig_filter_cfg_ar_valid),
        .cfg_aw_addr(sig_filter_cfg_aw_addr),
        .cfg_aw_ready(sig_filter_cfg_aw_ready),
        .cfg_aw_valid(sig_filter_cfg_aw_valid),
        .cfg_b_ready(sig_filter_cfg_b_ready),
        .cfg_b_resp(sig_filter_cfg_b_resp),
        .cfg_b_valid(sig_filter_cfg_b_valid),
        .cfg_r_data(sig_filter_cfg_r_data),
        .cfg_r_ready(sig_filter_cfg_r_ready),
        .cfg_r_resp(sig_filter_cfg_r_resp),
        .cfg_r_valid(sig_filter_cfg_r_valid),
        .cfg_w_data(sig_filter_cfg_w_data),
        .cfg_w_ready(sig_filter_cfg_w_ready),
        .cfg_w_strb(sig_filter_cfg_w_strb),
        .cfg_w_valid(sig_filter_cfg_w_valid),
        .din_data(sig_filter_din_data),
        .din_last(sig_filter_din_last),
        .din_ready(sig_filter_din_ready),
        .din_strb(sig_filter_din_strb),
        .din_valid(sig_filter_din_valid),
        .dout_data(sig_filter_dout_data),
        .dout_last(sig_filter_dout_last),
        .dout_ready(sig_filter_dout_ready),
        .dout_strb(sig_filter_dout_strb),
        .dout_valid(sig_filter_dout_valid),
        .headers_data(sig_filter_headers_data),
        .headers_last(sig_filter_headers_last),
        .headers_ready(sig_filter_headers_ready),
        .headers_strb(sig_filter_headers_strb),
        .headers_valid(sig_filter_headers_valid),
        .patternMatch_data(sig_filter_patternMatch_data),
        .patternMatch_last(sig_filter_patternMatch_last),
        .patternMatch_ready(sig_filter_patternMatch_ready),
        .patternMatch_strb(sig_filter_patternMatch_strb),
        .patternMatch_valid(sig_filter_patternMatch_valid)
        );


    gen_dout_splitCopy_0 #(.DATA_WIDTH(64),
        .IS_BIGENDIAN(0),
        .OUTPUTS(2)
        ) gen_dout_splitCopy_0_inst (.dataIn_data(sig_gen_dout_splitCopy_0_dataIn_data),
        .dataIn_last(sig_gen_dout_splitCopy_0_dataIn_last),
        .dataIn_ready(sig_gen_dout_splitCopy_0_dataIn_ready),
        .dataIn_strb(sig_gen_dout_splitCopy_0_dataIn_strb),
        .dataIn_valid(sig_gen_dout_splitCopy_0_dataIn_valid),
        .dataOut_data(sig_gen_dout_splitCopy_0_dataOut_data),
        .dataOut_last(sig_gen_dout_splitCopy_0_dataOut_last),
        .dataOut_ready(sig_gen_dout_splitCopy_0_dataOut_ready),
        .dataOut_strb(sig_gen_dout_splitCopy_0_dataOut_strb),
        .dataOut_valid(sig_gen_dout_splitCopy_0_dataOut_valid)
        );


    hfe #(.din_DATA_WIDTH(64),
        .din_IS_BIGENDIAN(0),
        .dout_DATA_WIDTH(64),
        .dout_IS_BIGENDIAN(0),
        .headers_DATA_WIDTH(64),
        .headers_IS_BIGENDIAN(0)
        ) hfe_inst (.din_data(sig_hfe_din_data),
        .din_last(sig_hfe_din_last),
        .din_ready(sig_hfe_din_ready),
        .din_strb(sig_hfe_din_strb),
        .din_valid(sig_hfe_din_valid),
        .dout_data(sig_hfe_dout_data),
        .dout_last(sig_hfe_dout_last),
        .dout_ready(sig_hfe_dout_ready),
        .dout_strb(sig_hfe_dout_strb),
        .dout_valid(sig_hfe_dout_valid),
        .headers_data(sig_hfe_headers_data),
        .headers_last(sig_hfe_headers_last),
        .headers_ready(sig_hfe_headers_ready),
        .headers_strb(sig_hfe_headers_strb),
        .headers_valid(sig_hfe_headers_valid)
        );


    patternMatch #(.din_DATA_WIDTH(64),
        .din_IS_BIGENDIAN(0),
        .match_DATA_WIDTH(64),
        .match_IS_BIGENDIAN(0)
        ) patternMatch_inst (.din_data(sig_patternMatch_din_data),
        .din_last(sig_patternMatch_din_last),
        .din_ready(sig_patternMatch_din_ready),
        .din_strb(sig_patternMatch_din_strb),
        .din_valid(sig_patternMatch_din_valid),
        .match_data(sig_patternMatch_match_data),
        .match_last(sig_patternMatch_match_last),
        .match_ready(sig_patternMatch_match_ready),
        .match_strb(sig_patternMatch_match_strb),
        .match_valid(sig_patternMatch_match_valid)
        );


    assign cfg_ar_ready = sig_filter_cfg_ar_ready;
    assign cfg_aw_ready = sig_filter_cfg_aw_ready;
    assign cfg_b_resp = sig_filter_cfg_b_resp;
    assign cfg_b_valid = sig_filter_cfg_b_valid;
    assign cfg_r_data = sig_filter_cfg_r_data;
    assign cfg_r_resp = sig_filter_cfg_r_resp;
    assign cfg_r_valid = sig_filter_cfg_r_valid;
    assign cfg_w_ready = sig_filter_cfg_w_ready;
    assign din_ready = sig_hfe_din_ready;
    assign export_data = sig_exporter_dout_data;
    assign export_last = sig_exporter_dout_last;
    assign export_strb = sig_exporter_dout_strb;
    assign export_valid = sig_exporter_dout_valid;
    assign sig_exporter_din_data = sig_filter_dout_data;
    assign sig_exporter_din_last = sig_filter_dout_last;
    assign sig_exporter_din_strb = sig_filter_dout_strb;
    assign sig_exporter_din_valid = sig_filter_dout_valid;
    assign sig_exporter_dout_ready = export_ready;
    assign sig_filter_cfg_ar_addr = cfg_ar_addr;
    assign sig_filter_cfg_ar_valid = cfg_ar_valid;
    assign sig_filter_cfg_aw_addr = cfg_aw_addr;
    assign sig_filter_cfg_aw_valid = cfg_aw_valid;
    assign sig_filter_cfg_b_ready = cfg_b_ready;
    assign sig_filter_cfg_r_ready = cfg_r_ready;
    assign sig_filter_cfg_w_data = cfg_w_data;
    assign sig_filter_cfg_w_strb = cfg_w_strb;
    assign sig_filter_cfg_w_valid = cfg_w_valid;
    assign sig_filter_din_data = sig_gen_dout_splitCopy_0_dataOut_data[127:64];
    assign sig_filter_din_last = sig_gen_dout_splitCopy_0_dataOut_last[1];
    assign sig_filter_din_strb = sig_gen_dout_splitCopy_0_dataOut_strb[15:8];
    assign sig_filter_din_valid = sig_gen_dout_splitCopy_0_dataOut_valid[1];
    assign sig_filter_dout_ready = sig_exporter_din_ready;
    assign sig_filter_headers_data = sig_hfe_headers_data;
    assign sig_filter_headers_last = sig_hfe_headers_last;
    assign sig_filter_headers_strb = sig_hfe_headers_strb;
    assign sig_filter_headers_valid = sig_hfe_headers_valid;
    assign sig_filter_patternMatch_data = sig_patternMatch_match_data;
    assign sig_filter_patternMatch_last = sig_patternMatch_match_last;
    assign sig_filter_patternMatch_strb = sig_patternMatch_match_strb;
    assign sig_filter_patternMatch_valid = sig_patternMatch_match_valid;
    assign sig_gen_dout_splitCopy_0_dataIn_data = sig_hfe_dout_data;
    assign sig_gen_dout_splitCopy_0_dataIn_last = sig_hfe_dout_last;
    assign sig_gen_dout_splitCopy_0_dataIn_strb = sig_hfe_dout_strb;
    assign sig_gen_dout_splitCopy_0_dataIn_valid = sig_hfe_dout_valid;
    always @(sig_patternMatch_din_ready) begin: assig_process_sig_gen_dout_splitCopy_0_dataOut_ready
        sig_gen_dout_splitCopy_0_dataOut_ready[0] <= sig_patternMatch_din_ready;
    end

    always @(sig_filter_din_ready) begin: assig_process_sig_gen_dout_splitCopy_0_dataOut_ready_0
        sig_gen_dout_splitCopy_0_dataOut_ready[1] <= sig_filter_din_ready;
    end

    assign sig_hfe_din_data = din_data;
    assign sig_hfe_din_last = din_last;
    assign sig_hfe_din_strb = din_strb;
    assign sig_hfe_din_valid = din_valid;
    assign sig_hfe_dout_ready = sig_gen_dout_splitCopy_0_dataIn_ready;
    assign sig_hfe_headers_ready = sig_filter_headers_ready;
    assign sig_patternMatch_din_data = sig_gen_dout_splitCopy_0_dataOut_data[63:0];
    assign sig_patternMatch_din_last = sig_gen_dout_splitCopy_0_dataOut_last[0];
    assign sig_patternMatch_din_strb = sig_gen_dout_splitCopy_0_dataOut_strb[7:0];
    assign sig_patternMatch_din_valid = sig_gen_dout_splitCopy_0_dataOut_valid[0];
    assign sig_patternMatch_match_ready = sig_filter_patternMatch_ready;
endmodule"""


netFilter_systemc = """#include <systemc.h>


SC_MODULE(hfe) {
    //interfaces
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> dout_data;
    sc_out<sc_uint<1>> dout_last;
    sc_in<sc_uint<1>> dout_ready;
    sc_out<sc_uint<8>> dout_strb;
    sc_out<sc_uint<1>> dout_valid;
    sc_out<sc_uint<64>> headers_data;
    sc_out<sc_uint<1>> headers_last;
    sc_in<sc_uint<1>> headers_ready;
    sc_out<sc_uint<8>> headers_strb;
    sc_out<sc_uint<1>> headers_valid;

    //processes inside this component
    void assig_process_din_ready() {
        din_ready.write('X');
    }
    void assig_process_dout_data() {
        dout_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_dout_last() {
        dout_last.write('X');
    }
    void assig_process_dout_strb() {
        dout_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_dout_valid() {
        dout_valid.write('X');
    }
    void assig_process_headers_data() {
        headers_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_headers_last() {
        headers_last.write('X');
    }
    void assig_process_headers_strb() {
        headers_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_headers_valid() {
        headers_valid.write('X');
    }

    SC_CTOR(hfe) {
        SC_METHOD(assig_process_din_ready);
        
        SC_METHOD(assig_process_dout_data);
        
        SC_METHOD(assig_process_dout_last);
        
        SC_METHOD(assig_process_dout_strb);
        
        SC_METHOD(assig_process_dout_valid);
        
        SC_METHOD(assig_process_headers_data);
        
        SC_METHOD(assig_process_headers_last);
        
        SC_METHOD(assig_process_headers_strb);
        
        SC_METHOD(assig_process_headers_valid);
        
    }
};
#include <systemc.h>


SC_MODULE(patternMatch) {
    //interfaces
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> match_data;
    sc_out<sc_uint<1>> match_last;
    sc_in<sc_uint<1>> match_ready;
    sc_out<sc_uint<8>> match_strb;
    sc_out<sc_uint<1>> match_valid;

    //processes inside this component
    void assig_process_din_ready() {
        din_ready.write('X');
    }
    void assig_process_match_data() {
        match_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_match_last() {
        match_last.write('X');
    }
    void assig_process_match_strb() {
        match_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_match_valid() {
        match_valid.write('X');
    }

    SC_CTOR(patternMatch) {
        SC_METHOD(assig_process_din_ready);
        
        SC_METHOD(assig_process_match_data);
        
        SC_METHOD(assig_process_match_last);
        
        SC_METHOD(assig_process_match_strb);
        
        SC_METHOD(assig_process_match_valid);
        
    }
};
#include <systemc.h>


SC_MODULE(filter) {
    //interfaces
    sc_in<sc_uint<32>> cfg_ar_addr;
    sc_out<sc_uint<1>> cfg_ar_ready;
    sc_in<sc_uint<1>> cfg_ar_valid;
    sc_in<sc_uint<32>> cfg_aw_addr;
    sc_out<sc_uint<1>> cfg_aw_ready;
    sc_in<sc_uint<1>> cfg_aw_valid;
    sc_in<sc_uint<1>> cfg_b_ready;
    sc_out<sc_uint<2>> cfg_b_resp;
    sc_out<sc_uint<1>> cfg_b_valid;
    sc_out<sc_uint<64>> cfg_r_data;
    sc_in<sc_uint<1>> cfg_r_ready;
    sc_out<sc_uint<2>> cfg_r_resp;
    sc_out<sc_uint<1>> cfg_r_valid;
    sc_in<sc_uint<64>> cfg_w_data;
    sc_out<sc_uint<1>> cfg_w_ready;
    sc_in<sc_uint<8>> cfg_w_strb;
    sc_in<sc_uint<1>> cfg_w_valid;
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> dout_data;
    sc_out<sc_uint<1>> dout_last;
    sc_in<sc_uint<1>> dout_ready;
    sc_out<sc_uint<8>> dout_strb;
    sc_out<sc_uint<1>> dout_valid;
    sc_in<sc_uint<64>> headers_data;
    sc_in<sc_uint<1>> headers_last;
    sc_out<sc_uint<1>> headers_ready;
    sc_in<sc_uint<8>> headers_strb;
    sc_in<sc_uint<1>> headers_valid;
    sc_in<sc_uint<64>> patternMatch_data;
    sc_in<sc_uint<1>> patternMatch_last;
    sc_out<sc_uint<1>> patternMatch_ready;
    sc_in<sc_uint<8>> patternMatch_strb;
    sc_in<sc_uint<1>> patternMatch_valid;

    //processes inside this component
    void assig_process_cfg_ar_ready() {
        cfg_ar_ready.write('X');
    }
    void assig_process_cfg_aw_ready() {
        cfg_aw_ready.write('X');
    }
    void assig_process_cfg_b_resp() {
        cfg_b_resp.write(sc_uint<2>("XX"));
    }
    void assig_process_cfg_b_valid() {
        cfg_b_valid.write('X');
    }
    void assig_process_cfg_r_data() {
        cfg_r_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_cfg_r_resp() {
        cfg_r_resp.write(sc_uint<2>("XX"));
    }
    void assig_process_cfg_r_valid() {
        cfg_r_valid.write('X');
    }
    void assig_process_cfg_w_ready() {
        cfg_w_ready.write('X');
    }
    void assig_process_din_ready() {
        din_ready.write('X');
    }
    void assig_process_dout_data() {
        dout_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_dout_last() {
        dout_last.write('X');
    }
    void assig_process_dout_strb() {
        dout_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_dout_valid() {
        dout_valid.write('X');
    }
    void assig_process_headers_ready() {
        headers_ready.write('X');
    }
    void assig_process_patternMatch_ready() {
        patternMatch_ready.write('X');
    }

    SC_CTOR(filter) {
        SC_METHOD(assig_process_cfg_ar_ready);
        
        SC_METHOD(assig_process_cfg_aw_ready);
        
        SC_METHOD(assig_process_cfg_b_resp);
        
        SC_METHOD(assig_process_cfg_b_valid);
        
        SC_METHOD(assig_process_cfg_r_data);
        
        SC_METHOD(assig_process_cfg_r_resp);
        
        SC_METHOD(assig_process_cfg_r_valid);
        
        SC_METHOD(assig_process_cfg_w_ready);
        
        SC_METHOD(assig_process_din_ready);
        
        SC_METHOD(assig_process_dout_data);
        
        SC_METHOD(assig_process_dout_last);
        
        SC_METHOD(assig_process_dout_strb);
        
        SC_METHOD(assig_process_dout_valid);
        
        SC_METHOD(assig_process_headers_ready);
        
        SC_METHOD(assig_process_patternMatch_ready);
        
    }
};
#include <systemc.h>


SC_MODULE(exporter) {
    //interfaces
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> dout_data;
    sc_out<sc_uint<1>> dout_last;
    sc_in<sc_uint<1>> dout_ready;
    sc_out<sc_uint<8>> dout_strb;
    sc_out<sc_uint<1>> dout_valid;

    //processes inside this component
    void assig_process_din_ready() {
        din_ready.write('X');
    }
    void assig_process_dout_data() {
        dout_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_dout_last() {
        dout_last.write('X');
    }
    void assig_process_dout_strb() {
        dout_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_dout_valid() {
        dout_valid.write('X');
    }

    SC_CTOR(exporter) {
        SC_METHOD(assig_process_din_ready);
        
        SC_METHOD(assig_process_dout_data);
        
        SC_METHOD(assig_process_dout_last);
        
        SC_METHOD(assig_process_dout_strb);
        
        SC_METHOD(assig_process_dout_valid);
        
    }
};
#include <systemc.h>


SC_MODULE(gen_dout_splitCopy_0) {
    //interfaces
    sc_in<sc_uint<64>> dataIn_data;
    sc_in<sc_uint<1>> dataIn_last;
    sc_out<sc_uint<1>> dataIn_ready;
    sc_in<sc_uint<8>> dataIn_strb;
    sc_in<sc_uint<1>> dataIn_valid;
    sc_out<sc_biguint<128>> dataOut_data;
    sc_out<sc_uint<2>> dataOut_last;
    sc_in<sc_uint<2>> dataOut_ready;
    sc_out<sc_uint<16>> dataOut_strb;
    sc_out<sc_uint<2>> dataOut_valid;

    //processes inside this component
    void assig_process_dataIn_ready() {
        dataIn_ready.write((dataOut_ready.read()[0]) & (dataOut_ready.read()[1]));
    }
    void assig_process_dataOut_data() {
        dataOut_data.range(64, 0).write(dataIn_data.read());
    }
    void assig_process_dataOut_data_0() {
        dataOut_data.range(128, 64).write(dataIn_data.read());
    }
    void assig_process_dataOut_last() {
        dataOut_last[0].write(dataIn_last.read());
    }
    void assig_process_dataOut_last_0() {
        dataOut_last[1].write(dataIn_last.read());
    }
    void assig_process_dataOut_strb() {
        dataOut_strb.range(8, 0).write(dataIn_strb.read());
    }
    void assig_process_dataOut_strb_0() {
        dataOut_strb.range(16, 8).write(dataIn_strb.read());
    }
    void assig_process_dataOut_valid() {
        dataOut_valid[0].write(dataIn_valid.read() & (dataOut_ready.read()[1]));
    }
    void assig_process_dataOut_valid_0() {
        dataOut_valid[1].write(dataIn_valid.read() & (dataOut_ready.read()[0]));
    }

    SC_CTOR(gen_dout_splitCopy_0) {
        SC_METHOD(assig_process_dataIn_ready);
        sensitive << dataOut_ready;
        SC_METHOD(assig_process_dataOut_data);
        sensitive << dataIn_data;
        SC_METHOD(assig_process_dataOut_data_0);
        sensitive << dataIn_data;
        SC_METHOD(assig_process_dataOut_last);
        sensitive << dataIn_last;
        SC_METHOD(assig_process_dataOut_last_0);
        sensitive << dataIn_last;
        SC_METHOD(assig_process_dataOut_strb);
        sensitive << dataIn_strb;
        SC_METHOD(assig_process_dataOut_strb_0);
        sensitive << dataIn_strb;
        SC_METHOD(assig_process_dataOut_valid);
        sensitive << dataIn_valid << dataOut_ready;
        SC_METHOD(assig_process_dataOut_valid_0);
        sensitive << dataIn_valid << dataOut_ready;
    }
};
/*

    This unit has actually no functionality it is just example of hierarchical design.
    
*/

#include <systemc.h>


SC_MODULE(NetFilter) {
    //interfaces
    sc_in<sc_uint<32>> cfg_ar_addr;
    sc_out<sc_uint<1>> cfg_ar_ready;
    sc_in<sc_uint<1>> cfg_ar_valid;
    sc_in<sc_uint<32>> cfg_aw_addr;
    sc_out<sc_uint<1>> cfg_aw_ready;
    sc_in<sc_uint<1>> cfg_aw_valid;
    sc_in<sc_uint<1>> cfg_b_ready;
    sc_out<sc_uint<2>> cfg_b_resp;
    sc_out<sc_uint<1>> cfg_b_valid;
    sc_out<sc_uint<64>> cfg_r_data;
    sc_in<sc_uint<1>> cfg_r_ready;
    sc_out<sc_uint<2>> cfg_r_resp;
    sc_out<sc_uint<1>> cfg_r_valid;
    sc_in<sc_uint<64>> cfg_w_data;
    sc_out<sc_uint<1>> cfg_w_ready;
    sc_in<sc_uint<8>> cfg_w_strb;
    sc_in<sc_uint<1>> cfg_w_valid;
    sc_in_clk clk;
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> export_data;
    sc_out<sc_uint<1>> export_last;
    sc_in<sc_uint<1>> export_ready;
    sc_out<sc_uint<8>> export_strb;
    sc_out<sc_uint<1>> export_valid;
    sc_in<sc_uint<1>> rst_n;

    //internal signals
    sc_signal<sc_uint<64>> sig_exporter_din_data;
    sc_signal<sc_uint<1>> sig_exporter_din_last;
    sc_signal<sc_uint<1>> sig_exporter_din_ready;
    sc_signal<sc_uint<8>> sig_exporter_din_strb;
    sc_signal<sc_uint<1>> sig_exporter_din_valid;
    sc_signal<sc_uint<64>> sig_exporter_dout_data;
    sc_signal<sc_uint<1>> sig_exporter_dout_last;
    sc_signal<sc_uint<1>> sig_exporter_dout_ready;
    sc_signal<sc_uint<8>> sig_exporter_dout_strb;
    sc_signal<sc_uint<1>> sig_exporter_dout_valid;
    sc_signal<sc_uint<32>> sig_filter_cfg_ar_addr;
    sc_signal<sc_uint<1>> sig_filter_cfg_ar_ready;
    sc_signal<sc_uint<1>> sig_filter_cfg_ar_valid;
    sc_signal<sc_uint<32>> sig_filter_cfg_aw_addr;
    sc_signal<sc_uint<1>> sig_filter_cfg_aw_ready;
    sc_signal<sc_uint<1>> sig_filter_cfg_aw_valid;
    sc_signal<sc_uint<1>> sig_filter_cfg_b_ready;
    sc_signal<sc_uint<2>> sig_filter_cfg_b_resp;
    sc_signal<sc_uint<1>> sig_filter_cfg_b_valid;
    sc_signal<sc_uint<64>> sig_filter_cfg_r_data;
    sc_signal<sc_uint<1>> sig_filter_cfg_r_ready;
    sc_signal<sc_uint<2>> sig_filter_cfg_r_resp;
    sc_signal<sc_uint<1>> sig_filter_cfg_r_valid;
    sc_signal<sc_uint<64>> sig_filter_cfg_w_data;
    sc_signal<sc_uint<1>> sig_filter_cfg_w_ready;
    sc_signal<sc_uint<8>> sig_filter_cfg_w_strb;
    sc_signal<sc_uint<1>> sig_filter_cfg_w_valid;
    sc_signal<sc_uint<64>> sig_filter_din_data;
    sc_signal<sc_uint<1>> sig_filter_din_last;
    sc_signal<sc_uint<1>> sig_filter_din_ready;
    sc_signal<sc_uint<8>> sig_filter_din_strb;
    sc_signal<sc_uint<1>> sig_filter_din_valid;
    sc_signal<sc_uint<64>> sig_filter_dout_data;
    sc_signal<sc_uint<1>> sig_filter_dout_last;
    sc_signal<sc_uint<1>> sig_filter_dout_ready;
    sc_signal<sc_uint<8>> sig_filter_dout_strb;
    sc_signal<sc_uint<1>> sig_filter_dout_valid;
    sc_signal<sc_uint<64>> sig_filter_headers_data;
    sc_signal<sc_uint<1>> sig_filter_headers_last;
    sc_signal<sc_uint<1>> sig_filter_headers_ready;
    sc_signal<sc_uint<8>> sig_filter_headers_strb;
    sc_signal<sc_uint<1>> sig_filter_headers_valid;
    sc_signal<sc_uint<64>> sig_filter_patternMatch_data;
    sc_signal<sc_uint<1>> sig_filter_patternMatch_last;
    sc_signal<sc_uint<1>> sig_filter_patternMatch_ready;
    sc_signal<sc_uint<8>> sig_filter_patternMatch_strb;
    sc_signal<sc_uint<1>> sig_filter_patternMatch_valid;
    sc_signal<sc_uint<64>> sig_gen_dout_splitCopy_0_dataIn_data;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataIn_last;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataIn_ready;
    sc_signal<sc_uint<8>> sig_gen_dout_splitCopy_0_dataIn_strb;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataIn_valid;
    sc_signal<sc_biguint<128>> sig_gen_dout_splitCopy_0_dataOut_data;
    sc_signal<sc_uint<2>> sig_gen_dout_splitCopy_0_dataOut_last;
    sc_signal<sc_uint<2>> sig_gen_dout_splitCopy_0_dataOut_ready;
    sc_signal<sc_uint<16>> sig_gen_dout_splitCopy_0_dataOut_strb;
    sc_signal<sc_uint<2>> sig_gen_dout_splitCopy_0_dataOut_valid;
    sc_signal<sc_uint<64>> sig_hfe_din_data;
    sc_signal<sc_uint<1>> sig_hfe_din_last;
    sc_signal<sc_uint<1>> sig_hfe_din_ready;
    sc_signal<sc_uint<8>> sig_hfe_din_strb;
    sc_signal<sc_uint<1>> sig_hfe_din_valid;
    sc_signal<sc_uint<64>> sig_hfe_dout_data;
    sc_signal<sc_uint<1>> sig_hfe_dout_last;
    sc_signal<sc_uint<1>> sig_hfe_dout_ready;
    sc_signal<sc_uint<8>> sig_hfe_dout_strb;
    sc_signal<sc_uint<1>> sig_hfe_dout_valid;
    sc_signal<sc_uint<64>> sig_hfe_headers_data;
    sc_signal<sc_uint<1>> sig_hfe_headers_last;
    sc_signal<sc_uint<1>> sig_hfe_headers_ready;
    sc_signal<sc_uint<8>> sig_hfe_headers_strb;
    sc_signal<sc_uint<1>> sig_hfe_headers_valid;
    sc_signal<sc_uint<64>> sig_patternMatch_din_data;
    sc_signal<sc_uint<1>> sig_patternMatch_din_last;
    sc_signal<sc_uint<1>> sig_patternMatch_din_ready;
    sc_signal<sc_uint<8>> sig_patternMatch_din_strb;
    sc_signal<sc_uint<1>> sig_patternMatch_din_valid;
    sc_signal<sc_uint<64>> sig_patternMatch_match_data;
    sc_signal<sc_uint<1>> sig_patternMatch_match_last;
    sc_signal<sc_uint<1>> sig_patternMatch_match_ready;
    sc_signal<sc_uint<8>> sig_patternMatch_match_strb;
    sc_signal<sc_uint<1>> sig_patternMatch_match_valid;

    //processes inside this component
    void assig_process_cfg_ar_ready() {
        cfg_ar_ready.write(sig_filter_cfg_ar_ready.read());
    }
    void assig_process_cfg_aw_ready() {
        cfg_aw_ready.write(sig_filter_cfg_aw_ready.read());
    }
    void assig_process_cfg_b_resp() {
        cfg_b_resp.write(sig_filter_cfg_b_resp.read());
    }
    void assig_process_cfg_b_valid() {
        cfg_b_valid.write(sig_filter_cfg_b_valid.read());
    }
    void assig_process_cfg_r_data() {
        cfg_r_data.write(sig_filter_cfg_r_data.read());
    }
    void assig_process_cfg_r_resp() {
        cfg_r_resp.write(sig_filter_cfg_r_resp.read());
    }
    void assig_process_cfg_r_valid() {
        cfg_r_valid.write(sig_filter_cfg_r_valid.read());
    }
    void assig_process_cfg_w_ready() {
        cfg_w_ready.write(sig_filter_cfg_w_ready.read());
    }
    void assig_process_din_ready() {
        din_ready.write(sig_hfe_din_ready.read());
    }
    void assig_process_export_data() {
        export_data.write(sig_exporter_dout_data.read());
    }
    void assig_process_export_last() {
        export_last.write(sig_exporter_dout_last.read());
    }
    void assig_process_export_strb() {
        export_strb.write(sig_exporter_dout_strb.read());
    }
    void assig_process_export_valid() {
        export_valid.write(sig_exporter_dout_valid.read());
    }
    void assig_process_sig_exporter_din_data() {
        sig_exporter_din_data.write(sig_filter_dout_data.read());
    }
    void assig_process_sig_exporter_din_last() {
        sig_exporter_din_last.write(sig_filter_dout_last.read());
    }
    void assig_process_sig_exporter_din_strb() {
        sig_exporter_din_strb.write(sig_filter_dout_strb.read());
    }
    void assig_process_sig_exporter_din_valid() {
        sig_exporter_din_valid.write(sig_filter_dout_valid.read());
    }
    void assig_process_sig_exporter_dout_ready() {
        sig_exporter_dout_ready.write(export_ready.read());
    }
    void assig_process_sig_filter_cfg_ar_addr() {
        sig_filter_cfg_ar_addr.write(cfg_ar_addr.read());
    }
    void assig_process_sig_filter_cfg_ar_valid() {
        sig_filter_cfg_ar_valid.write(cfg_ar_valid.read());
    }
    void assig_process_sig_filter_cfg_aw_addr() {
        sig_filter_cfg_aw_addr.write(cfg_aw_addr.read());
    }
    void assig_process_sig_filter_cfg_aw_valid() {
        sig_filter_cfg_aw_valid.write(cfg_aw_valid.read());
    }
    void assig_process_sig_filter_cfg_b_ready() {
        sig_filter_cfg_b_ready.write(cfg_b_ready.read());
    }
    void assig_process_sig_filter_cfg_r_ready() {
        sig_filter_cfg_r_ready.write(cfg_r_ready.read());
    }
    void assig_process_sig_filter_cfg_w_data() {
        sig_filter_cfg_w_data.write(cfg_w_data.read());
    }
    void assig_process_sig_filter_cfg_w_strb() {
        sig_filter_cfg_w_strb.write(cfg_w_strb.read());
    }
    void assig_process_sig_filter_cfg_w_valid() {
        sig_filter_cfg_w_valid.write(cfg_w_valid.read());
    }
    void assig_process_sig_filter_din_data() {
        sig_filter_din_data.write(sig_gen_dout_splitCopy_0_dataOut_data.read().range(128, 64));
    }
    void assig_process_sig_filter_din_last() {
        sig_filter_din_last.write(sig_gen_dout_splitCopy_0_dataOut_last.read()[1]);
    }
    void assig_process_sig_filter_din_strb() {
        sig_filter_din_strb.write(sig_gen_dout_splitCopy_0_dataOut_strb.read().range(16, 8));
    }
    void assig_process_sig_filter_din_valid() {
        sig_filter_din_valid.write(sig_gen_dout_splitCopy_0_dataOut_valid.read()[1]);
    }
    void assig_process_sig_filter_dout_ready() {
        sig_filter_dout_ready.write(sig_exporter_din_ready.read());
    }
    void assig_process_sig_filter_headers_data() {
        sig_filter_headers_data.write(sig_hfe_headers_data.read());
    }
    void assig_process_sig_filter_headers_last() {
        sig_filter_headers_last.write(sig_hfe_headers_last.read());
    }
    void assig_process_sig_filter_headers_strb() {
        sig_filter_headers_strb.write(sig_hfe_headers_strb.read());
    }
    void assig_process_sig_filter_headers_valid() {
        sig_filter_headers_valid.write(sig_hfe_headers_valid.read());
    }
    void assig_process_sig_filter_patternMatch_data() {
        sig_filter_patternMatch_data.write(sig_patternMatch_match_data.read());
    }
    void assig_process_sig_filter_patternMatch_last() {
        sig_filter_patternMatch_last.write(sig_patternMatch_match_last.read());
    }
    void assig_process_sig_filter_patternMatch_strb() {
        sig_filter_patternMatch_strb.write(sig_patternMatch_match_strb.read());
    }
    void assig_process_sig_filter_patternMatch_valid() {
        sig_filter_patternMatch_valid.write(sig_patternMatch_match_valid.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataIn_data() {
        sig_gen_dout_splitCopy_0_dataIn_data.write(sig_hfe_dout_data.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataIn_last() {
        sig_gen_dout_splitCopy_0_dataIn_last.write(sig_hfe_dout_last.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataIn_strb() {
        sig_gen_dout_splitCopy_0_dataIn_strb.write(sig_hfe_dout_strb.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataIn_valid() {
        sig_gen_dout_splitCopy_0_dataIn_valid.write(sig_hfe_dout_valid.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataOut_ready() {
        sig_gen_dout_splitCopy_0_dataOut_ready[0].write(sig_patternMatch_din_ready.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataOut_ready_0() {
        sig_gen_dout_splitCopy_0_dataOut_ready[1].write(sig_filter_din_ready.read());
    }
    void assig_process_sig_hfe_din_data() {
        sig_hfe_din_data.write(din_data.read());
    }
    void assig_process_sig_hfe_din_last() {
        sig_hfe_din_last.write(din_last.read());
    }
    void assig_process_sig_hfe_din_strb() {
        sig_hfe_din_strb.write(din_strb.read());
    }
    void assig_process_sig_hfe_din_valid() {
        sig_hfe_din_valid.write(din_valid.read());
    }
    void assig_process_sig_hfe_dout_ready() {
        sig_hfe_dout_ready.write(sig_gen_dout_splitCopy_0_dataIn_ready.read());
    }
    void assig_process_sig_hfe_headers_ready() {
        sig_hfe_headers_ready.write(sig_filter_headers_ready.read());
    }
    void assig_process_sig_patternMatch_din_data() {
        sig_patternMatch_din_data.write(sig_gen_dout_splitCopy_0_dataOut_data.read().range(64, 0));
    }
    void assig_process_sig_patternMatch_din_last() {
        sig_patternMatch_din_last.write(sig_gen_dout_splitCopy_0_dataOut_last.read()[0]);
    }
    void assig_process_sig_patternMatch_din_strb() {
        sig_patternMatch_din_strb.write(sig_gen_dout_splitCopy_0_dataOut_strb.read().range(8, 0));
    }
    void assig_process_sig_patternMatch_din_valid() {
        sig_patternMatch_din_valid.write(sig_gen_dout_splitCopy_0_dataOut_valid.read()[0]);
    }
    void assig_process_sig_patternMatch_match_ready() {
        sig_patternMatch_match_ready.write(sig_filter_patternMatch_ready.read());
    }

    // components inside this component

    exporter exporter_inst;
    filter filter_inst;
    gen_dout_splitCopy_0 gen_dout_splitCopy_0_inst;
    hfe hfe_inst;
    patternMatch patternMatch_inst;

    SC_CTOR(NetFilter) : exporter_inst("exporter_inst"), filter_inst("filter_inst"), gen_dout_splitCopy_0_inst("gen_dout_splitCopy_0_inst"), hfe_inst("hfe_inst"), patternMatch_inst("patternMatch_inst") {
        SC_METHOD(assig_process_cfg_ar_ready);
        sensitive << sig_filter_cfg_ar_ready;
        SC_METHOD(assig_process_cfg_aw_ready);
        sensitive << sig_filter_cfg_aw_ready;
        SC_METHOD(assig_process_cfg_b_resp);
        sensitive << sig_filter_cfg_b_resp;
        SC_METHOD(assig_process_cfg_b_valid);
        sensitive << sig_filter_cfg_b_valid;
        SC_METHOD(assig_process_cfg_r_data);
        sensitive << sig_filter_cfg_r_data;
        SC_METHOD(assig_process_cfg_r_resp);
        sensitive << sig_filter_cfg_r_resp;
        SC_METHOD(assig_process_cfg_r_valid);
        sensitive << sig_filter_cfg_r_valid;
        SC_METHOD(assig_process_cfg_w_ready);
        sensitive << sig_filter_cfg_w_ready;
        SC_METHOD(assig_process_din_ready);
        sensitive << sig_hfe_din_ready;
        SC_METHOD(assig_process_export_data);
        sensitive << sig_exporter_dout_data;
        SC_METHOD(assig_process_export_last);
        sensitive << sig_exporter_dout_last;
        SC_METHOD(assig_process_export_strb);
        sensitive << sig_exporter_dout_strb;
        SC_METHOD(assig_process_export_valid);
        sensitive << sig_exporter_dout_valid;
        SC_METHOD(assig_process_sig_exporter_din_data);
        sensitive << sig_filter_dout_data;
        SC_METHOD(assig_process_sig_exporter_din_last);
        sensitive << sig_filter_dout_last;
        SC_METHOD(assig_process_sig_exporter_din_strb);
        sensitive << sig_filter_dout_strb;
        SC_METHOD(assig_process_sig_exporter_din_valid);
        sensitive << sig_filter_dout_valid;
        SC_METHOD(assig_process_sig_exporter_dout_ready);
        sensitive << export_ready;
        SC_METHOD(assig_process_sig_filter_cfg_ar_addr);
        sensitive << cfg_ar_addr;
        SC_METHOD(assig_process_sig_filter_cfg_ar_valid);
        sensitive << cfg_ar_valid;
        SC_METHOD(assig_process_sig_filter_cfg_aw_addr);
        sensitive << cfg_aw_addr;
        SC_METHOD(assig_process_sig_filter_cfg_aw_valid);
        sensitive << cfg_aw_valid;
        SC_METHOD(assig_process_sig_filter_cfg_b_ready);
        sensitive << cfg_b_ready;
        SC_METHOD(assig_process_sig_filter_cfg_r_ready);
        sensitive << cfg_r_ready;
        SC_METHOD(assig_process_sig_filter_cfg_w_data);
        sensitive << cfg_w_data;
        SC_METHOD(assig_process_sig_filter_cfg_w_strb);
        sensitive << cfg_w_strb;
        SC_METHOD(assig_process_sig_filter_cfg_w_valid);
        sensitive << cfg_w_valid;
        SC_METHOD(assig_process_sig_filter_din_data);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_data;
        SC_METHOD(assig_process_sig_filter_din_last);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_last;
        SC_METHOD(assig_process_sig_filter_din_strb);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_strb;
        SC_METHOD(assig_process_sig_filter_din_valid);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_valid;
        SC_METHOD(assig_process_sig_filter_dout_ready);
        sensitive << sig_exporter_din_ready;
        SC_METHOD(assig_process_sig_filter_headers_data);
        sensitive << sig_hfe_headers_data;
        SC_METHOD(assig_process_sig_filter_headers_last);
        sensitive << sig_hfe_headers_last;
        SC_METHOD(assig_process_sig_filter_headers_strb);
        sensitive << sig_hfe_headers_strb;
        SC_METHOD(assig_process_sig_filter_headers_valid);
        sensitive << sig_hfe_headers_valid;
        SC_METHOD(assig_process_sig_filter_patternMatch_data);
        sensitive << sig_patternMatch_match_data;
        SC_METHOD(assig_process_sig_filter_patternMatch_last);
        sensitive << sig_patternMatch_match_last;
        SC_METHOD(assig_process_sig_filter_patternMatch_strb);
        sensitive << sig_patternMatch_match_strb;
        SC_METHOD(assig_process_sig_filter_patternMatch_valid);
        sensitive << sig_patternMatch_match_valid;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataIn_data);
        sensitive << sig_hfe_dout_data;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataIn_last);
        sensitive << sig_hfe_dout_last;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataIn_strb);
        sensitive << sig_hfe_dout_strb;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataIn_valid);
        sensitive << sig_hfe_dout_valid;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataOut_ready);
        sensitive << sig_patternMatch_din_ready;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataOut_ready_0);
        sensitive << sig_filter_din_ready;
        SC_METHOD(assig_process_sig_hfe_din_data);
        sensitive << din_data;
        SC_METHOD(assig_process_sig_hfe_din_last);
        sensitive << din_last;
        SC_METHOD(assig_process_sig_hfe_din_strb);
        sensitive << din_strb;
        SC_METHOD(assig_process_sig_hfe_din_valid);
        sensitive << din_valid;
        SC_METHOD(assig_process_sig_hfe_dout_ready);
        sensitive << sig_gen_dout_splitCopy_0_dataIn_ready;
        SC_METHOD(assig_process_sig_hfe_headers_ready);
        sensitive << sig_filter_headers_ready;
        SC_METHOD(assig_process_sig_patternMatch_din_data);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_data;
        SC_METHOD(assig_process_sig_patternMatch_din_last);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_last;
        SC_METHOD(assig_process_sig_patternMatch_din_strb);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_strb;
        SC_METHOD(assig_process_sig_patternMatch_din_valid);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_valid;
        SC_METHOD(assig_process_sig_patternMatch_match_ready);
        sensitive << sig_filter_patternMatch_ready;

        // connect ports
        exporter.din_data(sig_exporter_din_data);
        exporter.din_last(sig_exporter_din_last);
        exporter.din_ready(sig_exporter_din_ready);
        exporter.din_strb(sig_exporter_din_strb);
        exporter.din_valid(sig_exporter_din_valid);
        exporter.dout_data(sig_exporter_dout_data);
        exporter.dout_last(sig_exporter_dout_last);
        exporter.dout_ready(sig_exporter_dout_ready);
        exporter.dout_strb(sig_exporter_dout_strb);
        exporter.dout_valid(sig_exporter_dout_valid);
        filter.cfg_ar_addr(sig_filter_cfg_ar_addr);
        filter.cfg_ar_ready(sig_filter_cfg_ar_ready);
        filter.cfg_ar_valid(sig_filter_cfg_ar_valid);
        filter.cfg_aw_addr(sig_filter_cfg_aw_addr);
        filter.cfg_aw_ready(sig_filter_cfg_aw_ready);
        filter.cfg_aw_valid(sig_filter_cfg_aw_valid);
        filter.cfg_b_ready(sig_filter_cfg_b_ready);
        filter.cfg_b_resp(sig_filter_cfg_b_resp);
        filter.cfg_b_valid(sig_filter_cfg_b_valid);
        filter.cfg_r_data(sig_filter_cfg_r_data);
        filter.cfg_r_ready(sig_filter_cfg_r_ready);
        filter.cfg_r_resp(sig_filter_cfg_r_resp);
        filter.cfg_r_valid(sig_filter_cfg_r_valid);
        filter.cfg_w_data(sig_filter_cfg_w_data);
        filter.cfg_w_ready(sig_filter_cfg_w_ready);
        filter.cfg_w_strb(sig_filter_cfg_w_strb);
        filter.cfg_w_valid(sig_filter_cfg_w_valid);
        filter.din_data(sig_filter_din_data);
        filter.din_last(sig_filter_din_last);
        filter.din_ready(sig_filter_din_ready);
        filter.din_strb(sig_filter_din_strb);
        filter.din_valid(sig_filter_din_valid);
        filter.dout_data(sig_filter_dout_data);
        filter.dout_last(sig_filter_dout_last);
        filter.dout_ready(sig_filter_dout_ready);
        filter.dout_strb(sig_filter_dout_strb);
        filter.dout_valid(sig_filter_dout_valid);
        filter.headers_data(sig_filter_headers_data);
        filter.headers_last(sig_filter_headers_last);
        filter.headers_ready(sig_filter_headers_ready);
        filter.headers_strb(sig_filter_headers_strb);
        filter.headers_valid(sig_filter_headers_valid);
        filter.patternMatch_data(sig_filter_patternMatch_data);
        filter.patternMatch_last(sig_filter_patternMatch_last);
        filter.patternMatch_ready(sig_filter_patternMatch_ready);
        filter.patternMatch_strb(sig_filter_patternMatch_strb);
        filter.patternMatch_valid(sig_filter_patternMatch_valid);
        gen_dout_splitCopy_0.dataIn_data(sig_gen_dout_splitCopy_0_dataIn_data);
        gen_dout_splitCopy_0.dataIn_last(sig_gen_dout_splitCopy_0_dataIn_last);
        gen_dout_splitCopy_0.dataIn_ready(sig_gen_dout_splitCopy_0_dataIn_ready);
        gen_dout_splitCopy_0.dataIn_strb(sig_gen_dout_splitCopy_0_dataIn_strb);
        gen_dout_splitCopy_0.dataIn_valid(sig_gen_dout_splitCopy_0_dataIn_valid);
        gen_dout_splitCopy_0.dataOut_data(sig_gen_dout_splitCopy_0_dataOut_data);
        gen_dout_splitCopy_0.dataOut_last(sig_gen_dout_splitCopy_0_dataOut_last);
        gen_dout_splitCopy_0.dataOut_ready(sig_gen_dout_splitCopy_0_dataOut_ready);
        gen_dout_splitCopy_0.dataOut_strb(sig_gen_dout_splitCopy_0_dataOut_strb);
        gen_dout_splitCopy_0.dataOut_valid(sig_gen_dout_splitCopy_0_dataOut_valid);
        hfe.din_data(sig_hfe_din_data);
        hfe.din_last(sig_hfe_din_last);
        hfe.din_ready(sig_hfe_din_ready);
        hfe.din_strb(sig_hfe_din_strb);
        hfe.din_valid(sig_hfe_din_valid);
        hfe.dout_data(sig_hfe_dout_data);
        hfe.dout_last(sig_hfe_dout_last);
        hfe.dout_ready(sig_hfe_dout_ready);
        hfe.dout_strb(sig_hfe_dout_strb);
        hfe.dout_valid(sig_hfe_dout_valid);
        hfe.headers_data(sig_hfe_headers_data);
        hfe.headers_last(sig_hfe_headers_last);
        hfe.headers_ready(sig_hfe_headers_ready);
        hfe.headers_strb(sig_hfe_headers_strb);
        hfe.headers_valid(sig_hfe_headers_valid);
        patternMatch.din_data(sig_patternMatch_din_data);
        patternMatch.din_last(sig_patternMatch_din_last);
        patternMatch.din_ready(sig_patternMatch_din_ready);
        patternMatch.din_strb(sig_patternMatch_din_strb);
        patternMatch.din_valid(sig_patternMatch_din_valid);
        patternMatch.match_data(sig_patternMatch_match_data);
        patternMatch.match_last(sig_patternMatch_match_last);
        patternMatch.match_ready(sig_patternMatch_match_ready);
        patternMatch.match_strb(sig_patternMatch_match_strb);
        patternMatch.match_valid(sig_patternMatch_match_valid);
    }
};"""
