LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitReanamedPort5 IS
    PORT(
        b_eth_rx : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_eth_rx_vld : IN STD_LOGIC;
        b_eth_tx_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_eth_tx_last : OUT STD_LOGIC;
        b_eth_tx_ready : IN STD_LOGIC;
        b_eth_tx_valid : OUT STD_LOGIC;
        b_rx_last : IN STD_LOGIC;
        b_rx_ready : OUT STD_LOGIC;
        eth_rx : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        eth_rx_vld : OUT STD_LOGIC;
        eth_tx_data : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        eth_tx_last : IN STD_LOGIC;
        eth_tx_ready : OUT STD_LOGIC;
        eth_tx_valid : IN STD_LOGIC;
        rx_last : OUT STD_LOGIC;
        rx_ready : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitReanamedPort5 IS
BEGIN
    b_eth_tx_data <= eth_tx_data;
    b_eth_tx_last <= eth_tx_last;
    b_eth_tx_valid <= eth_tx_valid;
    b_rx_ready <= rx_ready;
    eth_rx <= b_eth_rx;
    eth_rx_vld <= b_eth_rx_vld;
    eth_tx_ready <= b_eth_tx_ready;
    rx_last <= b_rx_last;
END ARCHITECTURE;
