LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
ENTITY AxiReaderCore IS
    PORT(
        arRd : IN STD_LOGIC;
        arVld : IN STD_LOGIC;
        rRd : IN STD_LOGIC;
        rVld : IN STD_LOGIC;
        r_idle : OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AxiReaderCore IS
    TYPE rSt_t IS (rdIdle, rdData);
    SIGNAL rSt : rSt_t;
BEGIN
    assig_process_rSt: PROCESS(arRd, arVld, rRd, rVld)
    BEGIN
        IF arRd = '1' THEN
            IF arVld = '1' THEN
                rSt <= rdData;
            ELSE
                rSt <= rdIdle;
            END IF;
        ELSIF (rRd AND rVld) = '1' THEN
            rSt <= rdIdle;
        ELSE
            rSt <= rdData;
        END IF;
    END PROCESS;
    r_idle <= '1' WHEN (rSt = rdIdle) ELSE '0';
END ARCHITECTURE;
