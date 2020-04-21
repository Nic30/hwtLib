LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;

ENTITY AxiReaderCore IS
    PORT (arRd: IN STD_LOGIC;
        arVld: IN STD_LOGIC;
        rRd: IN STD_LOGIC;
        rSt: OUT rSt_t;
        rVld: IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AxiReaderCore IS
BEGIN
    assig_process_rSt: PROCESS (arRd, arVld, rRd, rVld)
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

END ARCHITECTURE;
