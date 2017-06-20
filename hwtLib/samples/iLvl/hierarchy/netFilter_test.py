#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.iLvl.hierarchy.netFilter import NetFilter
from hwt.synthesizer.shortcuts import toRtl
from hwtLib.tests.statementTrees import StatementTreesTC


expected = \
"""library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY hfe IS
    GENERIC ( 
    DIN_DATA_WIDTH : INTEGER := 64;
        DOUT_DATA_WIDTH : INTEGER := 64;
        HEADERS_DATA_WIDTH : INTEGER := 64 
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
    GENERIC ( 
    DIN_DATA_WIDTH : INTEGER := 64;
        MATCH_DATA_WIDTH : INTEGER := 64 
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
    GENERIC ( 
    CFG_ADDR_WIDTH : INTEGER := 32;
        CFG_DATA_WIDTH : INTEGER := 64;
        DIN_DATA_WIDTH : INTEGER := 64;
        DOUT_DATA_WIDTH : INTEGER := 64;
        HEADERS_DATA_WIDTH : INTEGER := 64;
        PATTERNMATCH_DATA_WIDTH : INTEGER := 64 
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
    GENERIC ( 
    DIN_DATA_WIDTH : INTEGER := 64;
        DOUT_DATA_WIDTH : INTEGER := 64 
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

ENTITY gen_dout_fork_0 IS
    GENERIC ( 
    DATA_WIDTH : INTEGER := 64;
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
END gen_dout_fork_0;

ARCHITECTURE rtl OF gen_dout_fork_0 IS
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
    GENERIC ( 
    CFG_ADDR_WIDTH : INTEGER := 32;
        DATA_WIDTH : INTEGER := 64 
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
    SIGNAL sig_gen_dout_fork_0_dataIn_data : STD_LOGIC_VECTOR(63 DOWNTO 0);
    SIGNAL sig_gen_dout_fork_0_dataIn_last : STD_LOGIC;
    SIGNAL sig_gen_dout_fork_0_dataIn_ready : STD_LOGIC;
    SIGNAL sig_gen_dout_fork_0_dataIn_strb : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_gen_dout_fork_0_dataIn_valid : STD_LOGIC;
    SIGNAL sig_gen_dout_fork_0_dataOut_data : STD_LOGIC_VECTOR(127 DOWNTO 0);
    SIGNAL sig_gen_dout_fork_0_dataOut_last : STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_gen_dout_fork_0_dataOut_ready : STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL sig_gen_dout_fork_0_dataOut_strb : STD_LOGIC_VECTOR(15 DOWNTO 0);
    SIGNAL sig_gen_dout_fork_0_dataOut_valid : STD_LOGIC_VECTOR(1 DOWNTO 0);
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
            DOUT_DATA_WIDTH : INTEGER := 64 
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
            DOUT_DATA_WIDTH : INTEGER := 64;
            HEADERS_DATA_WIDTH : INTEGER := 64;
            PATTERNMATCH_DATA_WIDTH : INTEGER := 64 
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
    COMPONENT gen_dout_fork_0 IS
       GENERIC (DATA_WIDTH : INTEGER := 64;
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
            DOUT_DATA_WIDTH : INTEGER := 64;
            HEADERS_DATA_WIDTH : INTEGER := 64 
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
            MATCH_DATA_WIDTH : INTEGER := 64 
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
            DOUT_DATA_WIDTH => 64 
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
            DOUT_DATA_WIDTH => 64,
            HEADERS_DATA_WIDTH => 64,
            PATTERNMATCH_DATA_WIDTH => 64 
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


    gen_dout_fork_0_inst : COMPONENT gen_dout_fork_0
        GENERIC MAP (DATA_WIDTH => 64,
            OUTPUTS => 2 
        )
        PORT MAP ( dataIn_data => sig_gen_dout_fork_0_dataIn_data,
             dataIn_last => sig_gen_dout_fork_0_dataIn_last,
             dataIn_ready => sig_gen_dout_fork_0_dataIn_ready,
             dataIn_strb => sig_gen_dout_fork_0_dataIn_strb,
             dataIn_valid => sig_gen_dout_fork_0_dataIn_valid,
             dataOut_data => sig_gen_dout_fork_0_dataOut_data,
             dataOut_last => sig_gen_dout_fork_0_dataOut_last,
             dataOut_ready => sig_gen_dout_fork_0_dataOut_ready,
             dataOut_strb => sig_gen_dout_fork_0_dataOut_strb,
             dataOut_valid => sig_gen_dout_fork_0_dataOut_valid
        );


    hfe_inst : COMPONENT hfe
        GENERIC MAP (DIN_DATA_WIDTH => 64,
            DOUT_DATA_WIDTH => 64,
            HEADERS_DATA_WIDTH => 64 
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
            MATCH_DATA_WIDTH => 64 
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
    sig_filter_din_data <= sig_gen_dout_fork_0_dataOut_data( 127 DOWNTO 64 ); 
    sig_filter_din_last <= sig_gen_dout_fork_0_dataOut_last( 1 ); 
    sig_filter_din_strb <= sig_gen_dout_fork_0_dataOut_strb( 15 DOWNTO 8 ); 
    sig_filter_din_valid <= sig_gen_dout_fork_0_dataOut_valid( 1 ); 
    sig_filter_dout_ready <= sig_exporter_din_ready; 
    sig_filter_headers_data <= sig_hfe_headers_data; 
    sig_filter_headers_last <= sig_hfe_headers_last; 
    sig_filter_headers_strb <= sig_hfe_headers_strb; 
    sig_filter_headers_valid <= sig_hfe_headers_valid; 
    sig_filter_patternMatch_data <= sig_patternMatch_match_data; 
    sig_filter_patternMatch_last <= sig_patternMatch_match_last; 
    sig_filter_patternMatch_strb <= sig_patternMatch_match_strb; 
    sig_filter_patternMatch_valid <= sig_patternMatch_match_valid; 
    sig_gen_dout_fork_0_dataIn_data <= sig_hfe_dout_data; 
    sig_gen_dout_fork_0_dataIn_last <= sig_hfe_dout_last; 
    sig_gen_dout_fork_0_dataIn_strb <= sig_hfe_dout_strb; 
    sig_gen_dout_fork_0_dataIn_valid <= sig_hfe_dout_valid; 
    sig_gen_dout_fork_0_dataOut_ready( 0 ) <= sig_patternMatch_din_ready; 
    sig_gen_dout_fork_0_dataOut_ready( 1 ) <= sig_filter_din_ready; 
    sig_hfe_din_data <= din_data; 
    sig_hfe_din_last <= din_last; 
    sig_hfe_din_strb <= din_strb; 
    sig_hfe_din_valid <= din_valid; 
    sig_hfe_dout_ready <= sig_gen_dout_fork_0_dataIn_ready; 
    sig_hfe_headers_ready <= sig_filter_headers_ready; 
    sig_patternMatch_din_data <= sig_gen_dout_fork_0_dataOut_data( 63 DOWNTO 0 ); 
    sig_patternMatch_din_last <= sig_gen_dout_fork_0_dataOut_last( 0 ); 
    sig_patternMatch_din_strb <= sig_gen_dout_fork_0_dataOut_strb( 7 DOWNTO 0 ); 
    sig_patternMatch_din_valid <= sig_gen_dout_fork_0_dataOut_valid( 0 ); 
    sig_patternMatch_match_ready <= sig_filter_patternMatch_ready; 
END ARCHITECTURE rtl;
"""


class NetFilterTC(SimTestCase):

    def test_serialization(self):
        u = NetFilter()
        StatementTreesTC.strStructureCmp(self, expected, toRtl(u))
        #print(toRtl(u))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NetFilterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
