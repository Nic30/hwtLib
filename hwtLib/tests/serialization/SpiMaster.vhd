LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Little endian encoded number to number in one-hot encoding
--
--    .. hwt-autodoc::
--    
ENTITY BinToOneHot IS
    GENERIC(
        DATA_WIDTH : INTEGER := 1
    );
    PORT(
        din : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        dout : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
        en : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF BinToOneHot IS
BEGIN
    dout(0) <= en;
    ASSERT DATA_WIDTH = 1 REPORT "Generated only for this value" SEVERITY error;
END ARCHITECTURE;
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Master for SPI interface
--
--    :ivar ~.SPI_FREQ_PESCALER: frequency prescaler to get SPI clk from main clk (Param)
--    :ivar ~.SS_WAIT_CLK_TICKS: number of SPI ticks to wait with SPI clk activation after slave select
--    :ivar ~.HAS_TX: if set true write part will be instantiated
--    :ivar ~.HAS_RX: if set true read part will be instantiated
--
--    :attention: this implementation expects that slaves are reading data on rising edge of SPI clk
--        and data from slaves are ready on risign edge as well
--        and SPI clk is kept high in idle
--        (most of them does but there are some exceptions)
--
--    .. hwt-autodoc::
--    
ENTITY SpiMaster IS
    GENERIC(
        FREQ : INTEGER := 100000000;
        HAS_MISO : BOOLEAN := TRUE;
        HAS_MOSI : BOOLEAN := TRUE;
        HAS_RX : BOOLEAN := TRUE;
        HAS_TX : BOOLEAN := TRUE;
        SLAVE_CNT : INTEGER := 1;
        SPI_DATA_WIDTH : INTEGER := 1;
        SPI_FREQ_PESCALER : INTEGER := 32;
        SS_WAIT_CLK_TICKS : INTEGER := 4
    );
    PORT(
        clk : IN STD_LOGIC;
        data_din : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        data_dout : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        data_last : IN STD_LOGIC;
        data_rd : OUT STD_LOGIC;
        data_slave : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        data_vld : IN STD_LOGIC;
        rst_n : IN STD_LOGIC;
        spi_clk : OUT STD_LOGIC;
        spi_cs : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
        spi_miso : IN STD_LOGIC;
        spi_mosi : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SpiMaster IS
    --
    --    Little endian encoded number to number in one-hot encoding
    --
    --    .. hwt-autodoc::
    --    
    COMPONENT BinToOneHot IS
        GENERIC(
            DATA_WIDTH : INTEGER := 1
        );
        PORT(
            din : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
            dout : OUT STD_LOGIC_VECTOR(0 DOWNTO 0);
            en : IN STD_LOGIC
        );
    END COMPONENT;
    SIGNAL clkIntern : STD_LOGIC := '1';
    SIGNAL clkIntern_next : STD_LOGIC;
    SIGNAL clkIntern_next_edgeDetect_last : STD_LOGIC := '1';
    SIGNAL clkIntern_next_edgeDetect_last_next : STD_LOGIC;
    SIGNAL clkIntern_next_falling : STD_LOGIC;
    SIGNAL clkIntern_next_rising : STD_LOGIC;
    SIGNAL clkOut : STD_LOGIC := '1';
    SIGNAL clkOut_next : STD_LOGIC;
    SIGNAL endOfWord : STD_LOGIC;
    SIGNAL endOfWordDelayed : STD_LOGIC := '0';
    SIGNAL endOfWordDelayed_next : STD_LOGIC;
    SIGNAL endOfWordtimerCntr256 : STD_LOGIC_VECTOR(7 DOWNTO 0) := X"FF";
    SIGNAL endOfWordtimerCntr256_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL endOfWordtimerTick256 : STD_LOGIC;
    SIGNAL rxReg : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL rxReg_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL sig_csDecoder_din : STD_LOGIC_VECTOR(0 DOWNTO 0);
    SIGNAL sig_csDecoder_dout : STD_LOGIC_VECTOR(0 DOWNTO 0);
    SIGNAL sig_csDecoder_en : STD_LOGIC;
    SIGNAL slaveSelectWaitRequired : STD_LOGIC := '1';
    SIGNAL slaveSelectWaitRequired_next : STD_LOGIC;
    SIGNAL timersRst : STD_LOGIC;
    SIGNAL txInitialized : STD_LOGIC := '0';
    SIGNAL txInitialized_next : STD_LOGIC;
    SIGNAL txReg : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL txReg_next : STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    csDecoder_inst: BinToOneHot GENERIC MAP(
        DATA_WIDTH => 1
    ) PORT MAP(
        din => sig_csDecoder_din,
        dout => sig_csDecoder_dout,
        en => sig_csDecoder_en
    );
    assig_process_clkIntern_next: PROCESS(clkIntern, data_vld, endOfWordDelayed, endOfWordtimerCntr256)
    BEGIN
        IF endOfWordtimerCntr256(3 DOWNTO 0) = X"0" AND (NOT endOfWordDelayed AND data_vld) = '1' THEN
            clkIntern_next <= NOT clkIntern;
        ELSE
            clkIntern_next <= clkIntern;
        END IF;
    END PROCESS;
    clkIntern_next_edgeDetect_last_next <= clkIntern_next;
    clkIntern_next_falling <= NOT clkIntern_next AND clkIntern_next_edgeDetect_last;
    clkIntern_next_rising <= clkIntern_next AND NOT clkIntern_next_edgeDetect_last;
    assig_process_clkOut_next: PROCESS(clkOut, data_vld, endOfWordDelayed, endOfWordtimerCntr256, slaveSelectWaitRequired)
    BEGIN
        IF NOT slaveSelectWaitRequired = '1' AND (endOfWordtimerCntr256(3 DOWNTO 0) = X"0" AND (NOT endOfWordDelayed AND data_vld) = '1') THEN
            clkOut_next <= NOT clkOut;
        ELSE
            clkOut_next <= clkOut;
        END IF;
    END PROCESS;
    data_din <= rxReg;
    data_rd <= endOfWordDelayed;
    endOfWord <= '1' WHEN (endOfWordtimerCntr256 = X"00" AND (NOT endOfWordDelayed AND data_vld) = '1' AND NOT timersRst = '1') ELSE '0';
    endOfWordDelayed_next <= endOfWordtimerTick256;
    assig_process_endOfWordtimerCntr256_next: PROCESS(data_vld, endOfWordDelayed, endOfWordtimerCntr256, timersRst)
        VARIABLE tmpTypeConv_0 : UNSIGNED(7 DOWNTO 0);
    BEGIN
        tmpTypeConv_0 := UNSIGNED(endOfWordtimerCntr256) - UNSIGNED'(X"01");
        IF timersRst = '1' OR ((NOT endOfWordDelayed AND data_vld) = '1' AND endOfWordtimerCntr256 = X"00") THEN
            endOfWordtimerCntr256_next <= X"FF";
        ELSIF (NOT endOfWordDelayed AND data_vld) = '1' THEN
            endOfWordtimerCntr256_next <= STD_LOGIC_VECTOR(tmpTypeConv_0);
        ELSE
            endOfWordtimerCntr256_next <= endOfWordtimerCntr256;
        END IF;
    END PROCESS;
    endOfWordtimerTick256 <= endOfWord;
    assig_process_rxReg_next: PROCESS(clkIntern_next_rising, rxReg, slaveSelectWaitRequired, spi_miso)
    BEGIN
        IF (clkIntern_next_rising AND NOT slaveSelectWaitRequired) = '1' THEN
            rxReg_next <= rxReg(6 DOWNTO 0) & spi_miso;
        ELSE
            rxReg_next <= rxReg;
        END IF;
    END PROCESS;
    sig_csDecoder_din <= data_slave;
    sig_csDecoder_en <= data_vld;
    assig_process_slaveSelectWaitRequired_next: PROCESS(data_last, data_vld, endOfWordDelayed, endOfWordtimerCntr256, endOfWordtimerTick256, slaveSelectWaitRequired)
    BEGIN
        IF endOfWordtimerTick256 = '1' THEN
            slaveSelectWaitRequired_next <= data_last;
        ELSIF endOfWordtimerCntr256(6 DOWNTO 0) = "0000000" AND (NOT endOfWordDelayed AND data_vld) = '1' THEN
            slaveSelectWaitRequired_next <= '0';
        ELSE
            slaveSelectWaitRequired_next <= slaveSelectWaitRequired;
        END IF;
    END PROCESS;
    spi_clk <= clkOut;
    spi_cs <= NOT sig_csDecoder_dout;
    spi_mosi <= txReg(7);
    timersRst <= '1' WHEN (NOT (NOT endOfWordDelayed AND data_vld) = '1' OR (slaveSelectWaitRequired = '1' AND (endOfWordtimerCntr256(6 DOWNTO 0) = "0000000" AND (NOT endOfWordDelayed AND data_vld) = '1'))) ELSE '0';
    assig_process_txInitialized: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst_n = '0' THEN
                txInitialized <= '0';
                slaveSelectWaitRequired <= '1';
                endOfWordtimerCntr256 <= X"FF";
                endOfWordDelayed <= '0';
                clkOut <= '1';
                clkIntern_next_edgeDetect_last <= '1';
                clkIntern <= '1';
            ELSE
                txInitialized <= txInitialized_next;
                slaveSelectWaitRequired <= slaveSelectWaitRequired_next;
                endOfWordtimerCntr256 <= endOfWordtimerCntr256_next;
                endOfWordDelayed <= endOfWordDelayed_next;
                clkOut <= clkOut_next;
                clkIntern_next_edgeDetect_last <= clkIntern_next_edgeDetect_last_next;
                clkIntern <= clkIntern_next;
            END IF;
        END IF;
    END PROCESS;
    assig_process_txInitialized_next: PROCESS(clkIntern_next_falling, data_dout, endOfWordDelayed, slaveSelectWaitRequired, txInitialized, txReg)
    BEGIN
        IF (clkIntern_next_falling AND NOT slaveSelectWaitRequired) = '1' THEN
            IF txInitialized = '1' THEN
                txReg_next <= txReg(6 DOWNTO 0) & '0';
                IF endOfWordDelayed = '1' THEN
                    txInitialized_next <= '0';
                ELSE
                    txInitialized_next <= txInitialized;
                END IF;
            ELSE
                txInitialized_next <= '1';
                txReg_next <= data_dout;
            END IF;
        ELSIF endOfWordDelayed = '1' THEN
            txInitialized_next <= '0';
            txReg_next <= txReg;
        ELSE
            txInitialized_next <= txInitialized;
            txReg_next <= txReg;
        END IF;
    END PROCESS;
    assig_process_txReg: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            txReg <= txReg_next;
            rxReg <= rxReg_next;
        END IF;
    END PROCESS;
    ASSERT FREQ = 100000000 REPORT "Generated only for this value" SEVERITY error;
    ASSERT HAS_MISO = TRUE REPORT "Generated only for this value" SEVERITY error;
    ASSERT HAS_MOSI = TRUE REPORT "Generated only for this value" SEVERITY error;
    ASSERT HAS_RX = TRUE REPORT "Generated only for this value" SEVERITY error;
    ASSERT HAS_TX = TRUE REPORT "Generated only for this value" SEVERITY error;
    ASSERT SLAVE_CNT = 1 REPORT "Generated only for this value" SEVERITY error;
    ASSERT SPI_DATA_WIDTH = 1 REPORT "Generated only for this value" SEVERITY error;
    ASSERT SPI_FREQ_PESCALER = 32 REPORT "Generated only for this value" SEVERITY error;
    ASSERT SS_WAIT_CLK_TICKS = 4 REPORT "Generated only for this value" SEVERITY error;
END ARCHITECTURE;
