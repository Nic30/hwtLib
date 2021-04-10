LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY SimpleUnitReanamedPort4 IS
    PORT(
        b_rx_data : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_rx_last : IN STD_LOGIC;
        b_rx_ready : OUT STD_LOGIC;
        b_rx_valid : IN STD_LOGIC;
        b_tx_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        b_tx_last : OUT STD_LOGIC;
        b_tx_ready : IN STD_LOGIC;
        b_tx_valid : OUT STD_LOGIC;
        rx_data : OUT STD_LOGIC_VECTOR(63 DOWNTO 0);
        rx_last : OUT STD_LOGIC;
        rx_ready : IN STD_LOGIC;
        rx_valid : OUT STD_LOGIC;
        tx_data : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        tx_last : IN STD_LOGIC;
        tx_ready : OUT STD_LOGIC;
        tx_valid : IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleUnitReanamedPort4 IS
BEGIN
    b_rx_ready <= rx_ready;
    b_tx_data <= tx_data;
    b_tx_last <= tx_last;
    b_tx_valid <= tx_valid;
    rx_data <= b_rx_data;
    rx_last <= b_rx_last;
    rx_valid <= b_rx_valid;
    tx_ready <= b_tx_ready;
END ARCHITECTURE;
