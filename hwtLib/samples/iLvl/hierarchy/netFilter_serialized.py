netFilter_vhdl = \
"""library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY hfe IS
    GENERIC (DIN_DATA_WIDTH : INTEGER := 64;
        DIN_IS_BIGENDIAN : BOOLEAN := False;
        DOUT_DATA_WIDTH : INTEGER := 64;
        DOUT_IS_BIGENDIAN : BOOLEAN := False;
        HEADERS_DATA_WIDTH : INTEGER := 64;
        HEADERS_IS_BIGENDIAN : BOOLEAN := False
    );
    PORT (din_data : IN STD_LOGIC_VECTOR(DIN_DATA_WIDTH - 1 DOWNTO 0);
        din_last : IN STD_LOGIC;
        din_ready : OUT STD_LOGIC;
        din_strb : IN STD_LOGIC_VECTOR((DIN_DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid : IN STD_LOGIC;
        dout_data : OUT STD_LOGIC_VECTOR(DOUT_DATA_WIDTH - 1 DOWNTO 0);
        dout_last : OUT STD_LOGIC;
        dout_ready : IN STD_LOGIC;
        dout_strb : OUT STD_LOGIC_VECTOR((DOUT_DATA_WIDTH / 8) - 1 DOWNTO 0);
        dout_valid : OUT STD_LOGIC;
        headers_data : OUT STD_LOGIC_VECTOR(HEADERS_DATA_WIDTH - 1 DOWNTO 0);
        headers_last : OUT STD_LOGIC;
        headers_ready : IN STD_LOGIC;
        headers_strb : OUT STD_LOGIC_VECTOR((HEADERS_DATA_WIDTH / 8) - 1 DOWNTO 0);
        headers_valid : OUT STD_LOGIC
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
    GENERIC (DIN_DATA_WIDTH : INTEGER := 64;
        DIN_IS_BIGENDIAN : BOOLEAN := False;
        MATCH_DATA_WIDTH : INTEGER := 64;
        MATCH_IS_BIGENDIAN : BOOLEAN := False
    );
    PORT (din_data : IN STD_LOGIC_VECTOR(DIN_DATA_WIDTH - 1 DOWNTO 0);
        din_last : IN STD_LOGIC;
        din_ready : OUT STD_LOGIC;
        din_strb : IN STD_LOGIC_VECTOR((DIN_DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid : IN STD_LOGIC;
        match_data : OUT STD_LOGIC_VECTOR(MATCH_DATA_WIDTH - 1 DOWNTO 0);
        match_last : OUT STD_LOGIC;
        match_ready : IN STD_LOGIC;
        match_strb : OUT STD_LOGIC_VECTOR((MATCH_DATA_WIDTH / 8) - 1 DOWNTO 0);
        match_valid : OUT STD_LOGIC
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
    GENERIC (CFG_ADDR_WIDTH : INTEGER := 32;
        CFG_DATA_WIDTH : INTEGER := 64;
        DIN_DATA_WIDTH : INTEGER := 64;
        DIN_IS_BIGENDIAN : BOOLEAN := False;
        DOUT_DATA_WIDTH : INTEGER := 64;
        DOUT_IS_BIGENDIAN : BOOLEAN := False;
        HEADERS_DATA_WIDTH : INTEGER := 64;
        HEADERS_IS_BIGENDIAN : BOOLEAN := False;
        PATTERNMATCH_DATA_WIDTH : INTEGER := 64;
        PATTERNMATCH_IS_BIGENDIAN : BOOLEAN := False
    );
    PORT (cfg_ar_addr : IN STD_LOGIC_VECTOR(CFG_ADDR_WIDTH - 1 DOWNTO 0);
        cfg_ar_ready : OUT STD_LOGIC;
        cfg_ar_valid : IN STD_LOGIC;
        cfg_aw_addr : IN STD_LOGIC_VECTOR(CFG_ADDR_WIDTH - 1 DOWNTO 0);
        cfg_aw_ready : OUT STD_LOGIC;
        cfg_aw_valid : IN STD_LOGIC;
        cfg_b_ready : IN STD_LOGIC;
        cfg_b_resp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        cfg_b_valid : OUT STD_LOGIC;
        cfg_r_data : OUT STD_LOGIC_VECTOR(CFG_DATA_WIDTH - 1 DOWNTO 0);
        cfg_r_ready : IN STD_LOGIC;
        cfg_r_resp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        cfg_r_valid : OUT STD_LOGIC;
        cfg_w_data : IN STD_LOGIC_VECTOR(CFG_DATA_WIDTH - 1 DOWNTO 0);
        cfg_w_ready : OUT STD_LOGIC;
        cfg_w_strb : IN STD_LOGIC_VECTOR((CFG_DATA_WIDTH / 8) - 1 DOWNTO 0);
        cfg_w_valid : IN STD_LOGIC;
        din_data : IN STD_LOGIC_VECTOR(DIN_DATA_WIDTH - 1 DOWNTO 0);
        din_last : IN STD_LOGIC;
        din_ready : OUT STD_LOGIC;
        din_strb : IN STD_LOGIC_VECTOR((DIN_DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid : IN STD_LOGIC;
        dout_data : OUT STD_LOGIC_VECTOR(DOUT_DATA_WIDTH - 1 DOWNTO 0);
        dout_last : OUT STD_LOGIC;
        dout_ready : IN STD_LOGIC;
        dout_strb : OUT STD_LOGIC_VECTOR((DOUT_DATA_WIDTH / 8) - 1 DOWNTO 0);
        dout_valid : OUT STD_LOGIC;
        headers_data : IN STD_LOGIC_VECTOR(HEADERS_DATA_WIDTH - 1 DOWNTO 0);
        headers_last : IN STD_LOGIC;
        headers_ready : OUT STD_LOGIC;
        headers_strb : IN STD_LOGIC_VECTOR((HEADERS_DATA_WIDTH / 8) - 1 DOWNTO 0);
        headers_valid : IN STD_LOGIC;
        patternMatch_data : IN STD_LOGIC_VECTOR(PATTERNMATCH_DATA_WIDTH - 1 DOWNTO 0);
        patternMatch_last : IN STD_LOGIC;
        patternMatch_ready : OUT STD_LOGIC;
        patternMatch_strb : IN STD_LOGIC_VECTOR((PATTERNMATCH_DATA_WIDTH / 8) - 1 DOWNTO 0);
        patternMatch_valid : IN STD_LOGIC
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
    GENERIC (DIN_DATA_WIDTH : INTEGER := 64;
        DIN_IS_BIGENDIAN : BOOLEAN := False;
        DOUT_DATA_WIDTH : INTEGER := 64;
        DOUT_IS_BIGENDIAN : BOOLEAN := False
    );
    PORT (din_data : IN STD_LOGIC_VECTOR(DIN_DATA_WIDTH - 1 DOWNTO 0);
        din_last : IN STD_LOGIC;
        din_ready : OUT STD_LOGIC;
        din_strb : IN STD_LOGIC_VECTOR((DIN_DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid : IN STD_LOGIC;
        dout_data : OUT STD_LOGIC_VECTOR(DOUT_DATA_WIDTH - 1 DOWNTO 0);
        dout_last : OUT STD_LOGIC;
        dout_ready : IN STD_LOGIC;
        dout_strb : OUT STD_LOGIC_VECTOR((DOUT_DATA_WIDTH / 8) - 1 DOWNTO 0);
        dout_valid : OUT STD_LOGIC
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
    GENERIC (DATA_WIDTH : INTEGER := 64;
        IS_BIGENDIAN : BOOLEAN := False;
        OUTPUTS : INTEGER := 2
    );
    PORT (dataIn_data : IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        dataIn_last : IN STD_LOGIC;
        dataIn_ready : OUT STD_LOGIC;
        dataIn_strb : IN STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        dataIn_valid : IN STD_LOGIC;
        dataOut_data : OUT STD_LOGIC_VECTOR((DATA_WIDTH * OUTPUTS) - 1 DOWNTO 0);
        dataOut_last : OUT STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0);
        dataOut_ready : IN STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0);
        dataOut_strb : OUT STD_LOGIC_VECTOR(((DATA_WIDTH / 8) * OUTPUTS) - 1 DOWNTO 0);
        dataOut_valid : OUT STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0)
    );
END gen_dout_splitCopy_0;

ARCHITECTURE rtl OF gen_dout_splitCopy_0 IS
BEGIN
    dataIn_ready <= (dataOut_ready( 0 )) AND (dataOut_ready( 1 ));
    dataOut_data( 63 DOWNTO 0 ) <= dataIn_data;
    dataOut_data( 127 DOWNTO 64 ) <= dataIn_data;
    dataOut_last( 0 ) <= dataIn_last;
    dataOut_last( 1 ) <= dataIn_last;
    dataOut_strb( 7 DOWNTO 0 ) <= dataIn_strb;
    dataOut_strb( 15 DOWNTO 8 ) <= dataIn_strb;
    dataOut_valid( 0 ) <= dataIn_valid AND (dataOut_ready( 1 ));
    dataOut_valid( 1 ) <= dataIn_valid AND (dataOut_ready( 0 ));
END ARCHITECTURE rtl;
--
--    This unit has actually no functionality it is just example of hierarchical design.
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY NetFilter IS
    GENERIC (CFG_ADDR_WIDTH : INTEGER := 32;
        DATA_WIDTH : INTEGER := 64;
        DIN_IS_BIGENDIAN : BOOLEAN := False;
        EXPORT_IS_BIGENDIAN : BOOLEAN := False
    );
    PORT (cfg_ar_addr : IN STD_LOGIC_VECTOR(CFG_ADDR_WIDTH - 1 DOWNTO 0);
        cfg_ar_ready : OUT STD_LOGIC;
        cfg_ar_valid : IN STD_LOGIC;
        cfg_aw_addr : IN STD_LOGIC_VECTOR(CFG_ADDR_WIDTH - 1 DOWNTO 0);
        cfg_aw_ready : OUT STD_LOGIC;
        cfg_aw_valid : IN STD_LOGIC;
        cfg_b_ready : IN STD_LOGIC;
        cfg_b_resp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        cfg_b_valid : OUT STD_LOGIC;
        cfg_r_data : OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        cfg_r_ready : IN STD_LOGIC;
        cfg_r_resp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        cfg_r_valid : OUT STD_LOGIC;
        cfg_w_data : IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        cfg_w_ready : OUT STD_LOGIC;
        cfg_w_strb : IN STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        cfg_w_valid : IN STD_LOGIC;
        clk : IN STD_LOGIC;
        din_data : IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        din_last : IN STD_LOGIC;
        din_ready : OUT STD_LOGIC;
        din_strb : IN STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        din_valid : IN STD_LOGIC;
        export_data : OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
        export_last : OUT STD_LOGIC;
        export_ready : IN STD_LOGIC;
        export_strb : OUT STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
        export_valid : OUT STD_LOGIC;
        rst_n : IN STD_LOGIC
    );
END NetFilter;

ARCHITECTURE rtl OF NetFilter IS
    SIGNAL sig_exporter_din_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_exporter_din_last : STD_LOGIC;
    SIGNAL sig_exporter_din_ready : STD_LOGIC;
    SIGNAL sig_exporter_din_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_exporter_din_valid : STD_LOGIC;
    SIGNAL sig_exporter_dout_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_exporter_dout_last : STD_LOGIC;
    SIGNAL sig_exporter_dout_ready : STD_LOGIC;
    SIGNAL sig_exporter_dout_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_exporter_dout_valid : STD_LOGIC;
    SIGNAL sig_filter_cfg_ar_addr : STD_LOGIC_VECTOR(31 DOWNTO 0);
    SIGNAL sig_filter_cfg_ar_ready : STD_LOGIC;
    SIGNAL sig_filter_cfg_ar_valid : STD_LOGIC;
    SIGNAL sig_filter_cfg_aw_addr : STD_LOGIC_VECTOR(31 DOWNTO 0);
    SIGNAL sig_filter_cfg_aw_ready : STD_LOGIC;
    SIGNAL sig_filter_cfg_aw_valid : STD_LOGIC;
    SIGNAL sig_filter_cfg_b_ready : STD_LOGIC;
    SIGNAL sig_filter_cfg_b_resp : STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_filter_cfg_b_valid : STD_LOGIC;
    SIGNAL sig_filter_cfg_r_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_cfg_r_ready : STD_LOGIC;
    SIGNAL sig_filter_cfg_r_resp : STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_filter_cfg_r_valid : STD_LOGIC;
    SIGNAL sig_filter_cfg_w_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_cfg_w_ready : STD_LOGIC;
    SIGNAL sig_filter_cfg_w_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_cfg_w_valid : STD_LOGIC;
    SIGNAL sig_filter_din_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_din_last : STD_LOGIC;
    SIGNAL sig_filter_din_ready : STD_LOGIC;
    SIGNAL sig_filter_din_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_din_valid : STD_LOGIC;
    SIGNAL sig_filter_dout_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_dout_last : STD_LOGIC;
    SIGNAL sig_filter_dout_ready : STD_LOGIC;
    SIGNAL sig_filter_dout_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_dout_valid : STD_LOGIC;
    SIGNAL sig_filter_headers_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_headers_last : STD_LOGIC;
    SIGNAL sig_filter_headers_ready : STD_LOGIC;
    SIGNAL sig_filter_headers_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_headers_valid : STD_LOGIC;
    SIGNAL sig_filter_patternMatch_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_filter_patternMatch_last : STD_LOGIC;
    SIGNAL sig_filter_patternMatch_ready : STD_LOGIC;
    SIGNAL sig_filter_patternMatch_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_filter_patternMatch_valid : STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_last : STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_ready : STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataIn_valid : STD_LOGIC;
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_data : STD_LOGIC_VECTOR(127 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_last : STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_ready : STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_strb : STD_LOGIC_VECTOR(15 DOWNTO 0);
    SIGNAL sig_gen_dout_splitCopy_0_dataOut_valid : STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_hfe_din_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_hfe_din_last : STD_LOGIC;
    SIGNAL sig_hfe_din_ready : STD_LOGIC;
    SIGNAL sig_hfe_din_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_hfe_din_valid : STD_LOGIC;
    SIGNAL sig_hfe_dout_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_hfe_dout_last : STD_LOGIC;
    SIGNAL sig_hfe_dout_ready : STD_LOGIC;
    SIGNAL sig_hfe_dout_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_hfe_dout_valid : STD_LOGIC;
    SIGNAL sig_hfe_headers_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_hfe_headers_last : STD_LOGIC;
    SIGNAL sig_hfe_headers_ready : STD_LOGIC;
    SIGNAL sig_hfe_headers_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_hfe_headers_valid : STD_LOGIC;
    SIGNAL sig_patternMatch_din_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_patternMatch_din_last : STD_LOGIC;
    SIGNAL sig_patternMatch_din_ready : STD_LOGIC;
    SIGNAL sig_patternMatch_din_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_patternMatch_din_valid : STD_LOGIC;
    SIGNAL sig_patternMatch_match_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_patternMatch_match_last : STD_LOGIC;
    SIGNAL sig_patternMatch_match_ready : STD_LOGIC;
    SIGNAL sig_patternMatch_match_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_patternMatch_match_valid : STD_LOGIC;
    COMPONENT exporter IS
       GENERIC (DIN_DATA_WIDTH : INTEGER := 64;
            DIN_IS_BIGENDIAN : BOOLEAN := False;
            DOUT_DATA_WIDTH : INTEGER := 64;
            DOUT_IS_BIGENDIAN : BOOLEAN := False
       );
       PORT (din_data : IN STD_LOGIC_VECTOR(DIN_DATA_WIDTH - 1 DOWNTO 0);
            din_last : IN STD_LOGIC;
            din_ready : OUT STD_LOGIC;
            din_strb : IN STD_LOGIC_VECTOR((DIN_DATA_WIDTH / 8) - 1 DOWNTO 0);
            din_valid : IN STD_LOGIC;
            dout_data : OUT STD_LOGIC_VECTOR(DOUT_DATA_WIDTH - 1 DOWNTO 0);
            dout_last : OUT STD_LOGIC;
            dout_ready : IN STD_LOGIC;
            dout_strb : OUT STD_LOGIC_VECTOR((DOUT_DATA_WIDTH / 8) - 1 DOWNTO 0);
            dout_valid : OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT filter IS
       GENERIC (CFG_ADDR_WIDTH : INTEGER := 32;
            CFG_DATA_WIDTH : INTEGER := 64;
            DIN_DATA_WIDTH : INTEGER := 64;
            DIN_IS_BIGENDIAN : BOOLEAN := False;
            DOUT_DATA_WIDTH : INTEGER := 64;
            DOUT_IS_BIGENDIAN : BOOLEAN := False;
            HEADERS_DATA_WIDTH : INTEGER := 64;
            HEADERS_IS_BIGENDIAN : BOOLEAN := False;
            PATTERNMATCH_DATA_WIDTH : INTEGER := 64;
            PATTERNMATCH_IS_BIGENDIAN : BOOLEAN := False
       );
       PORT (cfg_ar_addr : IN STD_LOGIC_VECTOR(CFG_ADDR_WIDTH - 1 DOWNTO 0);
            cfg_ar_ready : OUT STD_LOGIC;
            cfg_ar_valid : IN STD_LOGIC;
            cfg_aw_addr : IN STD_LOGIC_VECTOR(CFG_ADDR_WIDTH - 1 DOWNTO 0);
            cfg_aw_ready : OUT STD_LOGIC;
            cfg_aw_valid : IN STD_LOGIC;
            cfg_b_ready : IN STD_LOGIC;
            cfg_b_resp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
            cfg_b_valid : OUT STD_LOGIC;
            cfg_r_data : OUT STD_LOGIC_VECTOR(CFG_DATA_WIDTH - 1 DOWNTO 0);
            cfg_r_ready : IN STD_LOGIC;
            cfg_r_resp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
            cfg_r_valid : OUT STD_LOGIC;
            cfg_w_data : IN STD_LOGIC_VECTOR(CFG_DATA_WIDTH - 1 DOWNTO 0);
            cfg_w_ready : OUT STD_LOGIC;
            cfg_w_strb : IN STD_LOGIC_VECTOR((CFG_DATA_WIDTH / 8) - 1 DOWNTO 0);
            cfg_w_valid : IN STD_LOGIC;
            din_data : IN STD_LOGIC_VECTOR(DIN_DATA_WIDTH - 1 DOWNTO 0);
            din_last : IN STD_LOGIC;
            din_ready : OUT STD_LOGIC;
            din_strb : IN STD_LOGIC_VECTOR((DIN_DATA_WIDTH / 8) - 1 DOWNTO 0);
            din_valid : IN STD_LOGIC;
            dout_data : OUT STD_LOGIC_VECTOR(DOUT_DATA_WIDTH - 1 DOWNTO 0);
            dout_last : OUT STD_LOGIC;
            dout_ready : IN STD_LOGIC;
            dout_strb : OUT STD_LOGIC_VECTOR((DOUT_DATA_WIDTH / 8) - 1 DOWNTO 0);
            dout_valid : OUT STD_LOGIC;
            headers_data : IN STD_LOGIC_VECTOR(HEADERS_DATA_WIDTH - 1 DOWNTO 0);
            headers_last : IN STD_LOGIC;
            headers_ready : OUT STD_LOGIC;
            headers_strb : IN STD_LOGIC_VECTOR((HEADERS_DATA_WIDTH / 8) - 1 DOWNTO 0);
            headers_valid : IN STD_LOGIC;
            patternMatch_data : IN STD_LOGIC_VECTOR(PATTERNMATCH_DATA_WIDTH - 1 DOWNTO 0);
            patternMatch_last : IN STD_LOGIC;
            patternMatch_ready : OUT STD_LOGIC;
            patternMatch_strb : IN STD_LOGIC_VECTOR((PATTERNMATCH_DATA_WIDTH / 8) - 1 DOWNTO 0);
            patternMatch_valid : IN STD_LOGIC
       );
    END COMPONENT;

    COMPONENT gen_dout_splitCopy_0 IS
       GENERIC (DATA_WIDTH : INTEGER := 64;
            IS_BIGENDIAN : BOOLEAN := False;
            OUTPUTS : INTEGER := 2
       );
       PORT (dataIn_data : IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
            dataIn_last : IN STD_LOGIC;
            dataIn_ready : OUT STD_LOGIC;
            dataIn_strb : IN STD_LOGIC_VECTOR((DATA_WIDTH / 8) - 1 DOWNTO 0);
            dataIn_valid : IN STD_LOGIC;
            dataOut_data : OUT STD_LOGIC_VECTOR((DATA_WIDTH * OUTPUTS) - 1 DOWNTO 0);
            dataOut_last : OUT STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0);
            dataOut_ready : IN STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0);
            dataOut_strb : OUT STD_LOGIC_VECTOR(((DATA_WIDTH / 8) * OUTPUTS) - 1 DOWNTO 0);
            dataOut_valid : OUT STD_LOGIC_VECTOR(OUTPUTS - 1 DOWNTO 0)
       );
    END COMPONENT;

    COMPONENT hfe IS
       GENERIC (DIN_DATA_WIDTH : INTEGER := 64;
            DIN_IS_BIGENDIAN : BOOLEAN := False;
            DOUT_DATA_WIDTH : INTEGER := 64;
            DOUT_IS_BIGENDIAN : BOOLEAN := False;
            HEADERS_DATA_WIDTH : INTEGER := 64;
            HEADERS_IS_BIGENDIAN : BOOLEAN := False
       );
       PORT (din_data : IN STD_LOGIC_VECTOR(DIN_DATA_WIDTH - 1 DOWNTO 0);
            din_last : IN STD_LOGIC;
            din_ready : OUT STD_LOGIC;
            din_strb : IN STD_LOGIC_VECTOR((DIN_DATA_WIDTH / 8) - 1 DOWNTO 0);
            din_valid : IN STD_LOGIC;
            dout_data : OUT STD_LOGIC_VECTOR(DOUT_DATA_WIDTH - 1 DOWNTO 0);
            dout_last : OUT STD_LOGIC;
            dout_ready : IN STD_LOGIC;
            dout_strb : OUT STD_LOGIC_VECTOR((DOUT_DATA_WIDTH / 8) - 1 DOWNTO 0);
            dout_valid : OUT STD_LOGIC;
            headers_data : OUT STD_LOGIC_VECTOR(HEADERS_DATA_WIDTH - 1 DOWNTO 0);
            headers_last : OUT STD_LOGIC;
            headers_ready : IN STD_LOGIC;
            headers_strb : OUT STD_LOGIC_VECTOR((HEADERS_DATA_WIDTH / 8) - 1 DOWNTO 0);
            headers_valid : OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT patternMatch IS
       GENERIC (DIN_DATA_WIDTH : INTEGER := 64;
            DIN_IS_BIGENDIAN : BOOLEAN := False;
            MATCH_DATA_WIDTH : INTEGER := 64;
            MATCH_IS_BIGENDIAN : BOOLEAN := False
       );
       PORT (din_data : IN STD_LOGIC_VECTOR(DIN_DATA_WIDTH - 1 DOWNTO 0);
            din_last : IN STD_LOGIC;
            din_ready : OUT STD_LOGIC;
            din_strb : IN STD_LOGIC_VECTOR((DIN_DATA_WIDTH / 8) - 1 DOWNTO 0);
            din_valid : IN STD_LOGIC;
            match_data : OUT STD_LOGIC_VECTOR(MATCH_DATA_WIDTH - 1 DOWNTO 0);
            match_last : OUT STD_LOGIC;
            match_ready : IN STD_LOGIC;
            match_strb : OUT STD_LOGIC_VECTOR((MATCH_DATA_WIDTH / 8) - 1 DOWNTO 0);
            match_valid : OUT STD_LOGIC
       );
    END COMPONENT;

BEGIN
    exporter_inst : COMPONENT exporter
        GENERIC MAP (DIN_DATA_WIDTH => 64,
            DIN_IS_BIGENDIAN => False,
            DOUT_DATA_WIDTH => 64,
            DOUT_IS_BIGENDIAN => False
        )
        PORT MAP ( din_data => sig_exporter_din_data,
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

    filter_inst : COMPONENT filter
        GENERIC MAP (CFG_ADDR_WIDTH => 32,
            CFG_DATA_WIDTH => 64,
            DIN_DATA_WIDTH => 64,
            DIN_IS_BIGENDIAN => False,
            DOUT_DATA_WIDTH => 64,
            DOUT_IS_BIGENDIAN => False,
            HEADERS_DATA_WIDTH => 64,
            HEADERS_IS_BIGENDIAN => False,
            PATTERNMATCH_DATA_WIDTH => 64,
            PATTERNMATCH_IS_BIGENDIAN => False
        )
        PORT MAP ( cfg_ar_addr => sig_filter_cfg_ar_addr,
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

    gen_dout_splitCopy_0_inst : COMPONENT gen_dout_splitCopy_0
        GENERIC MAP (DATA_WIDTH => 64,
            IS_BIGENDIAN => False,
            OUTPUTS => 2
        )
        PORT MAP ( dataIn_data => sig_gen_dout_splitCopy_0_dataIn_data,
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

    hfe_inst : COMPONENT hfe
        GENERIC MAP (DIN_DATA_WIDTH => 64,
            DIN_IS_BIGENDIAN => False,
            DOUT_DATA_WIDTH => 64,
            DOUT_IS_BIGENDIAN => False,
            HEADERS_DATA_WIDTH => 64,
            HEADERS_IS_BIGENDIAN => False
        )
        PORT MAP ( din_data => sig_hfe_din_data,
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

    patternMatch_inst : COMPONENT patternMatch
        GENERIC MAP (DIN_DATA_WIDTH => 64,
            DIN_IS_BIGENDIAN => False,
            MATCH_DATA_WIDTH => 64,
            MATCH_IS_BIGENDIAN => False
        )
        PORT MAP ( din_data => sig_patternMatch_din_data,
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
    sig_filter_din_data <= sig_gen_dout_splitCopy_0_dataOut_data( 127 DOWNTO 64 );
    sig_filter_din_last <= sig_gen_dout_splitCopy_0_dataOut_last( 1 );
    sig_filter_din_strb <= sig_gen_dout_splitCopy_0_dataOut_strb( 15 DOWNTO 8 );
    sig_filter_din_valid <= sig_gen_dout_splitCopy_0_dataOut_valid( 1 );
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
    sig_gen_dout_splitCopy_0_dataOut_ready( 0 ) <= sig_patternMatch_din_ready;
    sig_gen_dout_splitCopy_0_dataOut_ready( 1 ) <= sig_filter_din_ready;
    sig_hfe_din_data <= din_data;
    sig_hfe_din_last <= din_last;
    sig_hfe_din_strb <= din_strb;
    sig_hfe_din_valid <= din_valid;
    sig_hfe_dout_ready <= sig_gen_dout_splitCopy_0_dataIn_ready;
    sig_hfe_headers_ready <= sig_filter_headers_ready;
    sig_patternMatch_din_data <= sig_gen_dout_splitCopy_0_dataOut_data( 63 DOWNTO 0 );
    sig_patternMatch_din_last <= sig_gen_dout_splitCopy_0_dataOut_last( 0 );
    sig_patternMatch_din_strb <= sig_gen_dout_splitCopy_0_dataOut_strb( 7 DOWNTO 0 );
    sig_patternMatch_din_valid <= sig_gen_dout_splitCopy_0_dataOut_valid( 0 );
    sig_patternMatch_match_ready <= sig_filter_patternMatch_ready;
END ARCHITECTURE rtl;"""


netFilter_verilog = """module hfe #(parameter  DIN_DATA_WIDTH = 64,
        parameter  DIN_IS_BIGENDIAN = 0,
        parameter  DOUT_DATA_WIDTH = 64,
        parameter  DOUT_IS_BIGENDIAN = 0,
        parameter  HEADERS_DATA_WIDTH = 64,
        parameter  HEADERS_IS_BIGENDIAN = 0
    )(input [DIN_DATA_WIDTH- 1:0] din_data,
        input  din_last,
        output  din_ready,
        input [DIN_DATA_WIDTH / 8- 1:0] din_strb,
        input  din_valid,
        output [DOUT_DATA_WIDTH- 1:0] dout_data,
        output  dout_last,
        input  dout_ready,
        output [DOUT_DATA_WIDTH / 8- 1:0] dout_strb,
        output  dout_valid,
        output [HEADERS_DATA_WIDTH- 1:0] headers_data,
        output  headers_last,
        input  headers_ready,
        output [HEADERS_DATA_WIDTH / 8- 1:0] headers_strb,
        output  headers_valid
    );

    assign din_ready = 2'bx; 
    assign dout_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; 
    assign dout_last = 2'bx; 
    assign dout_strb = 8'bxxxxxxxx; 
    assign dout_valid = 2'bx; 
    assign headers_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; 
    assign headers_last = 2'bx; 
    assign headers_strb = 8'bxxxxxxxx; 
    assign headers_valid = 2'bx; 
endmodule
module patternMatch #(parameter  DIN_DATA_WIDTH = 64,
        parameter  DIN_IS_BIGENDIAN = 0,
        parameter  MATCH_DATA_WIDTH = 64,
        parameter  MATCH_IS_BIGENDIAN = 0
    )(input [DIN_DATA_WIDTH- 1:0] din_data,
        input  din_last,
        output  din_ready,
        input [DIN_DATA_WIDTH / 8- 1:0] din_strb,
        input  din_valid,
        output [MATCH_DATA_WIDTH- 1:0] match_data,
        output  match_last,
        input  match_ready,
        output [MATCH_DATA_WIDTH / 8- 1:0] match_strb,
        output  match_valid
    );

    assign din_ready = 2'bx; 
    assign match_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; 
    assign match_last = 2'bx; 
    assign match_strb = 8'bxxxxxxxx; 
    assign match_valid = 2'bx; 
endmodule
module filter #(parameter  CFG_ADDR_WIDTH = 32,
        parameter  CFG_DATA_WIDTH = 64,
        parameter  DIN_DATA_WIDTH = 64,
        parameter  DIN_IS_BIGENDIAN = 0,
        parameter  DOUT_DATA_WIDTH = 64,
        parameter  DOUT_IS_BIGENDIAN = 0,
        parameter  HEADERS_DATA_WIDTH = 64,
        parameter  HEADERS_IS_BIGENDIAN = 0,
        parameter  PATTERNMATCH_DATA_WIDTH = 64,
        parameter  PATTERNMATCH_IS_BIGENDIAN = 0
    )(input [CFG_ADDR_WIDTH- 1:0] cfg_ar_addr,
        output  cfg_ar_ready,
        input  cfg_ar_valid,
        input [CFG_ADDR_WIDTH- 1:0] cfg_aw_addr,
        output  cfg_aw_ready,
        input  cfg_aw_valid,
        input  cfg_b_ready,
        output [1:0] cfg_b_resp,
        output  cfg_b_valid,
        output [CFG_DATA_WIDTH- 1:0] cfg_r_data,
        input  cfg_r_ready,
        output [1:0] cfg_r_resp,
        output  cfg_r_valid,
        input [CFG_DATA_WIDTH- 1:0] cfg_w_data,
        output  cfg_w_ready,
        input [CFG_DATA_WIDTH / 8- 1:0] cfg_w_strb,
        input  cfg_w_valid,
        input [DIN_DATA_WIDTH- 1:0] din_data,
        input  din_last,
        output  din_ready,
        input [DIN_DATA_WIDTH / 8- 1:0] din_strb,
        input  din_valid,
        output [DOUT_DATA_WIDTH- 1:0] dout_data,
        output  dout_last,
        input  dout_ready,
        output [DOUT_DATA_WIDTH / 8- 1:0] dout_strb,
        output  dout_valid,
        input [HEADERS_DATA_WIDTH- 1:0] headers_data,
        input  headers_last,
        output  headers_ready,
        input [HEADERS_DATA_WIDTH / 8- 1:0] headers_strb,
        input  headers_valid,
        input [PATTERNMATCH_DATA_WIDTH- 1:0] patternMatch_data,
        input  patternMatch_last,
        output  patternMatch_ready,
        input [PATTERNMATCH_DATA_WIDTH / 8- 1:0] patternMatch_strb,
        input  patternMatch_valid
    );

    assign cfg_ar_ready = 2'bx; 
    assign cfg_aw_ready = 2'bx; 
    assign cfg_b_resp = 2'bxx; 
    assign cfg_b_valid = 2'bx; 
    assign cfg_r_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; 
    assign cfg_r_resp = 2'bxx; 
    assign cfg_r_valid = 2'bx; 
    assign cfg_w_ready = 2'bx; 
    assign din_ready = 2'bx; 
    assign dout_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; 
    assign dout_last = 2'bx; 
    assign dout_strb = 8'bxxxxxxxx; 
    assign dout_valid = 2'bx; 
    assign headers_ready = 2'bx; 
    assign patternMatch_ready = 2'bx; 
endmodule
module exporter #(parameter  DIN_DATA_WIDTH = 64,
        parameter  DIN_IS_BIGENDIAN = 0,
        parameter  DOUT_DATA_WIDTH = 64,
        parameter  DOUT_IS_BIGENDIAN = 0
    )(input [DIN_DATA_WIDTH- 1:0] din_data,
        input  din_last,
        output  din_ready,
        input [DIN_DATA_WIDTH / 8- 1:0] din_strb,
        input  din_valid,
        output [DOUT_DATA_WIDTH- 1:0] dout_data,
        output  dout_last,
        input  dout_ready,
        output [DOUT_DATA_WIDTH / 8- 1:0] dout_strb,
        output  dout_valid
    );

    assign din_ready = 2'bx; 
    assign dout_data = 64'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; 
    assign dout_last = 2'bx; 
    assign dout_strb = 8'bxxxxxxxx; 
    assign dout_valid = 2'bx; 
endmodule
module gen_dout_splitCopy_0 #(parameter  DATA_WIDTH = 64,
        parameter  IS_BIGENDIAN = 0,
        parameter  OUTPUTS = 2
    )(input [DATA_WIDTH- 1:0] dataIn_data,
        input  dataIn_last,
        output  dataIn_ready,
        input [DATA_WIDTH / 8- 1:0] dataIn_strb,
        input  dataIn_valid,
        output reg [DATA_WIDTH * OUTPUTS- 1:0] dataOut_data,
        output reg [OUTPUTS- 1:0] dataOut_last,
        input [OUTPUTS- 1:0] dataOut_ready,
        output reg [DATA_WIDTH / 8 * OUTPUTS- 1:0] dataOut_strb,
        output reg [OUTPUTS- 1:0] dataOut_valid
    );

    assign dataIn_ready = (dataOut_ready[ 0 ]) & (dataOut_ready[ 1 ]); 
    always @(dataIn_data) begin: assig_process_dataOut_data
        dataOut_data[ 63:0 ] = dataIn_data;
    end

    always @(dataIn_data) begin: assig_process_dataOut_data_0
        dataOut_data[ 127:64 ] = dataIn_data;
    end

    always @(dataIn_last) begin: assig_process_dataOut_last
        dataOut_last[ 0 ] = dataIn_last;
    end

    always @(dataIn_last) begin: assig_process_dataOut_last_0
        dataOut_last[ 1 ] = dataIn_last;
    end

    always @(dataIn_strb) begin: assig_process_dataOut_strb
        dataOut_strb[ 7:0 ] = dataIn_strb;
    end

    always @(dataIn_strb) begin: assig_process_dataOut_strb_0
        dataOut_strb[ 15:8 ] = dataIn_strb;
    end

    always @(dataIn_valid or dataOut_ready) begin: assig_process_dataOut_valid
        dataOut_valid[ 0 ] = dataIn_valid & (dataOut_ready[ 1 ]);
    end

    always @(dataIn_valid or dataOut_ready) begin: assig_process_dataOut_valid_0
        dataOut_valid[ 1 ] = dataIn_valid & (dataOut_ready[ 0 ]);
    end

endmodule
/*

    This unit has actually no functionality it is just example of hierarchical design.
    
*/
module NetFilter #(parameter  CFG_ADDR_WIDTH = 32,
        parameter  DATA_WIDTH = 64,
        parameter  DIN_IS_BIGENDIAN = 0,
        parameter  EXPORT_IS_BIGENDIAN = 0
    )(input [CFG_ADDR_WIDTH- 1:0] cfg_ar_addr,
        output  cfg_ar_ready,
        input  cfg_ar_valid,
        input [CFG_ADDR_WIDTH- 1:0] cfg_aw_addr,
        output  cfg_aw_ready,
        input  cfg_aw_valid,
        input  cfg_b_ready,
        output [1:0] cfg_b_resp,
        output  cfg_b_valid,
        output [DATA_WIDTH- 1:0] cfg_r_data,
        input  cfg_r_ready,
        output [1:0] cfg_r_resp,
        output  cfg_r_valid,
        input [DATA_WIDTH- 1:0] cfg_w_data,
        output  cfg_w_ready,
        input [DATA_WIDTH / 8- 1:0] cfg_w_strb,
        input  cfg_w_valid,
        input  clk,
        input [DATA_WIDTH- 1:0] din_data,
        input  din_last,
        output  din_ready,
        input [DATA_WIDTH / 8- 1:0] din_strb,
        input  din_valid,
        output [DATA_WIDTH- 1:0] export_data,
        output  export_last,
        input  export_ready,
        output [DATA_WIDTH / 8- 1:0] export_strb,
        output  export_valid,
        input  rst_n
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
    exporter  #(.DIN_DATA_WIDTH(64),
        .DIN_IS_BIGENDIAN(0),
        .DOUT_DATA_WIDTH(64),
        .DOUT_IS_BIGENDIAN(0) 
        )exporter_inst (.din_data(sig_exporter_din_data),
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


    filter  #(.CFG_ADDR_WIDTH(32),
        .CFG_DATA_WIDTH(64),
        .DIN_DATA_WIDTH(64),
        .DIN_IS_BIGENDIAN(0),
        .DOUT_DATA_WIDTH(64),
        .DOUT_IS_BIGENDIAN(0),
        .HEADERS_DATA_WIDTH(64),
        .HEADERS_IS_BIGENDIAN(0),
        .PATTERNMATCH_DATA_WIDTH(64),
        .PATTERNMATCH_IS_BIGENDIAN(0) 
        )filter_inst (.cfg_ar_addr(sig_filter_cfg_ar_addr),
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


    gen_dout_splitCopy_0  #(.DATA_WIDTH(64),
        .IS_BIGENDIAN(0),
        .OUTPUTS(2) 
        )gen_dout_splitCopy_0_inst (.dataIn_data(sig_gen_dout_splitCopy_0_dataIn_data),
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


    hfe  #(.DIN_DATA_WIDTH(64),
        .DIN_IS_BIGENDIAN(0),
        .DOUT_DATA_WIDTH(64),
        .DOUT_IS_BIGENDIAN(0),
        .HEADERS_DATA_WIDTH(64),
        .HEADERS_IS_BIGENDIAN(0) 
        )hfe_inst (.din_data(sig_hfe_din_data),
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


    patternMatch  #(.DIN_DATA_WIDTH(64),
        .DIN_IS_BIGENDIAN(0),
        .MATCH_DATA_WIDTH(64),
        .MATCH_IS_BIGENDIAN(0) 
        )patternMatch_inst (.din_data(sig_patternMatch_din_data),
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
    assign sig_filter_din_data = sig_gen_dout_splitCopy_0_dataOut_data[ 127:64 ]; 
    assign sig_filter_din_last = sig_gen_dout_splitCopy_0_dataOut_last[ 1 ]; 
    assign sig_filter_din_strb = sig_gen_dout_splitCopy_0_dataOut_strb[ 15:8 ]; 
    assign sig_filter_din_valid = sig_gen_dout_splitCopy_0_dataOut_valid[ 1 ]; 
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
        sig_gen_dout_splitCopy_0_dataOut_ready[ 0 ] = sig_patternMatch_din_ready;
    end

    always @(sig_filter_din_ready) begin: assig_process_sig_gen_dout_splitCopy_0_dataOut_ready_0
        sig_gen_dout_splitCopy_0_dataOut_ready[ 1 ] = sig_filter_din_ready;
    end

    assign sig_hfe_din_data = din_data; 
    assign sig_hfe_din_last = din_last; 
    assign sig_hfe_din_strb = din_strb; 
    assign sig_hfe_din_valid = din_valid; 
    assign sig_hfe_dout_ready = sig_gen_dout_splitCopy_0_dataIn_ready; 
    assign sig_hfe_headers_ready = sig_filter_headers_ready; 
    assign sig_patternMatch_din_data = sig_gen_dout_splitCopy_0_dataOut_data[ 63:0 ]; 
    assign sig_patternMatch_din_last = sig_gen_dout_splitCopy_0_dataOut_last[ 0 ]; 
    assign sig_patternMatch_din_strb = sig_gen_dout_splitCopy_0_dataOut_strb[ 7:0 ]; 
    assign sig_patternMatch_din_valid = sig_gen_dout_splitCopy_0_dataOut_valid[ 0 ]; 
    assign sig_patternMatch_match_ready = sig_filter_patternMatch_ready; 
endmodule"""
