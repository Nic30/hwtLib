--
--    Example which is using switch statement to create multiplexer
--
--    .. hwt-schematic::
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SwitchStmUnit IS
    PORT (a: IN STD_LOGIC;
        b: IN STD_LOGIC;
        c: IN STD_LOGIC;
        out_0: OUT STD_LOGIC;
        sel: IN STD_LOGIC_VECTOR(2 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SwitchStmUnit IS
BEGIN
    assig_process_out: PROCESS (a, b, c, sel)
    BEGIN
        CASE sel IS
        WHEN "000" =>
            out_0 <= a;
        WHEN "001" =>
            out_0 <= b;
        WHEN "010" =>
            out_0 <= c;
        WHEN OTHERS =>
            out_0 <= '0';
        END CASE;
    END PROCESS;

END ARCHITECTURE;
