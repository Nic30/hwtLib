LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;
--
--    Every HW component class has to be derived from Unit class
--
--    .. hwt-autodoc::
--    
ENTITY Showcase0 IS
    PORT(
        a : IN UNSIGNED(31 DOWNTO 0);
        b : IN SIGNED(31 DOWNTO 0);
        c : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
        clk : IN STD_LOGIC;
        cmp_0 : OUT STD_LOGIC;
        cmp_1 : OUT STD_LOGIC;
        cmp_2 : OUT STD_LOGIC;
        cmp_3 : OUT STD_LOGIC;
        cmp_4 : OUT STD_LOGIC;
        cmp_5 : OUT STD_LOGIC;
        contOut : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
        d : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        e : IN STD_LOGIC;
        f : OUT STD_LOGIC;
        fitted : OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
        g : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        h : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        i : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        j : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        k : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
        out_0 : OUT STD_LOGIC;
        output : OUT STD_LOGIC;
        rst_n : IN STD_LOGIC;
        sc_signal : OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF Showcase0 IS
    TYPE arr_t_0 IS ARRAY (3 DOWNTO 0) OF SIGNED(7 DOWNTO 0);
    TYPE arr_t_1 IS ARRAY (3 DOWNTO 0) OF UNSIGNED(7 DOWNTO 0);
    CONSTANT const_private_signal : UNSIGNED(31 DOWNTO 0) := UNSIGNED'(X"0000007B");
    SIGNAL fallingEdgeRam : arr_t_0;
    SIGNAL r : STD_LOGIC := '0';
    SIGNAL r_0 : STD_LOGIC_VECTOR(1 DOWNTO 0) := "00";
    SIGNAL r_1 : STD_LOGIC_VECTOR(1 DOWNTO 0) := "00";
    SIGNAL r_next : STD_LOGIC;
    SIGNAL r_next_0 : STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL r_next_1 : STD_LOGIC_VECTOR(1 DOWNTO 0);
    CONSTANT rom : arr_t_1 := (
        UNSIGNED'(X"00"),
        UNSIGNED'(X"01"),
        UNSIGNED'(X"02"),
        UNSIGNED'(X"03"));
BEGIN
    assig_process_c: PROCESS(a, b)
        VARIABLE tmpTypeConv_0 : UNSIGNED(31 DOWNTO 0);
    BEGIN
        tmpTypeConv_0 := a + UNSIGNED(b);
        c <= STD_LOGIC_VECTOR(tmpTypeConv_0);
    END PROCESS;
    cmp_0 <= '1' WHEN (a < UNSIGNED'(X"00000004")) ELSE '0';
    cmp_1 <= '1' WHEN (a > UNSIGNED'(X"00000004")) ELSE '0';
    cmp_2 <= '1' WHEN (b <= SIGNED'(X"00000004")) ELSE '0';
    cmp_3 <= '1' WHEN (b >= SIGNED'(X"00000004")) ELSE '0';
    cmp_4 <= '1' WHEN (b /= SIGNED'(X"00000004")) ELSE '0';
    cmp_5 <= '1' WHEN (b = SIGNED'(X"00000004")) ELSE '0';
    contOut <= STD_LOGIC_VECTOR(const_private_signal);
    f <= r;
    assig_process_fallingEdgeRam: PROCESS(clk)
        VARIABLE tmpTypeConv_0 : UNSIGNED(7 DOWNTO 0);
        VARIABLE tmpTypeConv_1 : UNSIGNED(7 DOWNTO 0);
        VARIABLE tmpTypeConv_2 : SIGNED(7 DOWNTO 0);
    BEGIN
        tmpTypeConv_0 := a(7 DOWNTO 0);
        tmpTypeConv_1 := UNSIGNED(tmpTypeConv_2);
        tmpTypeConv_2 := fallingEdgeRam(TO_INTEGER(UNSIGNED(r_1)));
        IF FALLING_EDGE(clk) THEN
            fallingEdgeRam(TO_INTEGER(UNSIGNED(r_1))) <= SIGNED(tmpTypeConv_0);
            k <= X"000000" & STD_LOGIC_VECTOR(tmpTypeConv_1);
        END IF;
    END PROCESS;
    assig_process_fitted: PROCESS(a)
        VARIABLE tmpTypeConv_0 : UNSIGNED(15 DOWNTO 0);
    BEGIN
        tmpTypeConv_0 := a(15 DOWNTO 0);
        fitted <= STD_LOGIC_VECTOR(tmpTypeConv_0);
    END PROCESS;
    assig_process_g: PROCESS(a, b)
        VARIABLE tmpTypeConv_0 : UNSIGNED(5 DOWNTO 0);
    BEGIN
        tmpTypeConv_0 := a(5 DOWNTO 0);
        g <= (a(1) AND b(1)) & ((a(0) XOR b(0)) OR a(1)) & STD_LOGIC_VECTOR(tmpTypeConv_0);
    END PROCESS;
    assig_process_h: PROCESS(a, r)
    BEGIN
        IF a(2) = '1' THEN
            IF r = '1' THEN
                h <= X"00";
            ELSIF a(1) = '1' THEN
                h <= X"01";
            ELSE
                h <= X"02";
            END IF;
        END IF;
    END PROCESS;
    assig_process_j: PROCESS(clk)
        VARIABLE tmpTypeConv_0 : UNSIGNED(7 DOWNTO 0);
    BEGIN
        tmpTypeConv_0 := rom(TO_INTEGER(UNSIGNED(r_1)));
        IF RISING_EDGE(clk) THEN
            j <= STD_LOGIC_VECTOR(tmpTypeConv_0);
        END IF;
    END PROCESS;
    out_0 <= '0';
    output <= 'X';
    assig_process_r: PROCESS(clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst_n = '0' THEN
                r_1 <= "00";
                r_0 <= "00";
                r <= '0';
            ELSE
                r_1 <= r_next_1;
                r_0 <= r_next_0;
                r <= r_next;
            END IF;
        END IF;
    END PROCESS;
    r_next_0 <= i;
    r_next_1 <= r_0;
    assig_process_r_next_1: PROCESS(e, r)
    BEGIN
        IF NOT r = '1' THEN
            r_next <= e;
        ELSE
            r_next <= r;
        END IF;
    END PROCESS;
    assig_process_sc_signal: PROCESS(a)
    BEGIN
        CASE a IS
            WHEN UNSIGNED'(X"00000001") =>
                sc_signal <= X"00";
            WHEN UNSIGNED'(X"00000002") =>
                sc_signal <= X"01";
            WHEN UNSIGNED'(X"00000003") =>
                sc_signal <= X"03";
            WHEN OTHERS =>
                sc_signal <= X"04";
        END CASE;
    END PROCESS;
END ARCHITECTURE;
