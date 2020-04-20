library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY EmptyUnitWithSpi IS
    PORT (spi_clk: IN STD_LOGIC;
        spi_cs: IN STD_LOGIC_VECTOR(0 DOWNTO 0);
        spi_miso: OUT STD_LOGIC;
        spi_mosi: IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF EmptyUnitWithSpi IS
BEGIN
    spi_miso <= 'X';
END ARCHITECTURE;
