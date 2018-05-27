#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect, If, Concat, Switch
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.types.ctypes import uint32_t, int32_t, uint8_t, int8_t


def foo(condition0, statements, condition1, fallback0, fallback1):
    """
    Python functions used as macro
    """
    return If(condition0,
              statements
           ).Elif(condition1,
              fallback0,
           ).Else(
              fallback1
           )


class Showcase0(Unit):
    """
    Every HW component class has to be derived from Unit class (any kind of inheritance supported)
    """
    def __init__(self):
        # constructor can be overloaded but parent one has to be called
        super(Showcase0, self).__init__()

    def _declr(self):
        """
        In this function collecting of public interfaces is performed
        on every attribute assignment. Instances of Interface or Unit are recognized
        by Unit instance and are used as public interface of this unit.

        Direction of interfaces is resolved by access from inside of this unit
        and you do not have to care about it.
        """
        self.a = Signal(dtype=uint32_t)
        self.b = Signal(dtype=int32_t)

        # behavior same as uint32_t (which is Bits(32, signed=False))
        self.c = Signal(dtype=Bits(32))
        # VectSignal is just shortcut for Signal(dtype=Bits(...))
        self.fitted = VectSignal(16)
        self.contOut = VectSignal(32)

        # this signal will have no driver and it will be considered to be an input
        self.d = VectSignal(32)

        # names of public ports can not be same because they need to be accessible from parent
        self.e = Signal()
        self.f = Signal()
        self.g = VectSignal(8)

        # this function just instantiate clk and rstn interface
        # main purpose is to unify names of clock and reset signals
        addClkRstn(self)

        # Unit will not care for object which are not instance of Interface or Unit,
        # other object has to be registered manually
        self.cmp = [Signal() for _ in range(6)]
        self._registerArray("cmp", self.cmp)

        self.h = VectSignal(8)
        self.i = VectSignal(2)
        self.j = VectSignal(8)

        # collision with hdl keywords are automatically resolved and fixed
        # as well as case sensitivity care and other collisions in target HDL
        self.out = Signal()
        self.output = Signal()
        self.sc_signal = VectSignal(8)

        self.k = VectSignal(32)

    def _impl(self):
        """
        Purpose of this method
        In this method all public interfaces and configuration
        has been made and they can not be edited.
        """
        # create local variable to make code shorter
        a = self.a
        b = self.b

        # "call" is overloaded to do assignment
        # it means c = a + b in target HDL
        # type conversion is can be done by _auto_cast or _reinterpret_cast method call
        self.c(a + b._auto_cast(a._dtype))

        # width of signals is not same, this would raise TypeError on regular assignment,
        # this behavior can be overriden by calling connect with fit=True
        connect(a, self.fitted, fit=True)

        # every signal/value has _dtype attribute which is parent type
        # most of the types have physical size, bit_lenght returns size of this type in bits
        assert self.a._dtype.bit_length() == 32

        # it is possible to create signal explicitly by calling ._sig method
        # result of every operator is signal
        const_private_signal = self._sig("const_private_signal", dtype=uint32_t, defVal=123)
        self.contOut(const_private_signal)

        # this signal will be optimized out because it has no effect on any output
        # self.d will remain because it is part of interface
        self._sig("optimizedOut", dtype=uint32_t, defVal=123)

        # by _reg function usual d-register can be instantiated
        # to be able to use this this unit has to have clock defined 
        # (you can force any signal as clock if you call self._ctx._reg directly)
        # default type is BIT
        r = self._reg("r", defVal=0)

        # HDL If statement is object
        # ~ is negation operator
        If(~r,
           # you can directly assign to register and it will assign to its next value
           # (assigned value appears in it in second clk tick)
           r(self.e)
        )

        # again signals has to affect output or they will be optimized out
        self.f(r)

        # instead of and, or, xor use &, |, ^ because they are overridden to do the job
        tmp0 = a[1] & b[1]
        tmp1 = (a[0] ^ b[0]) | a[1]

        # bit concatenation is done by Concat function, python like slicing supported
        self.g(Concat(tmp0, tmp1, a[6:]))

        # results of comparison operators assigned to bits of cmp signal
        cmp = self.cmp
        cmp[0](a < 4)
        cmp[1](a > 4)
        cmp[2](b <= 4)
        cmp[3](b >= 4)
        cmp[4](b != 4)
        # _eq() is used as ==,
        # overriding == would have many unintended consequences in python
        # (it would make all signals unhasable)
        cmp[5](b._eq(4))

        h = self.h
        # all statements are just objects
        statements0 = h(0)
        statements1 = h(1)
        statements2 = h(2)
        statements3 = foo(r, statements0, a[1], statements1, statements2)
        assert isinstance(statements3, If)
        If(a[2],
            # also when there is not value specified in the branch of dataflow
            # (in this case there is missing else branch) this signal will become latched
            statements3
        )

        # all statements like If, Switch, For and others are in hwt.code

        # names of generated signals are patched to avoid collisions automatically
        r0 = self._reg("r", Bits(2), defVal=0)
        r1 = self._reg("r", Bits(2), defVal=0)

        r0(self.i)
        r1(r0)

        # type of signal can be array as well, this allow to create memories like BRAM...
        # rom will be synchronous ROM in this case
        rom = self._sig("rom", uint8_t[4], defVal=[i for i in range(4)])

        If(self.clk._onRisingEdge(),
           self.j(rom[r1])
        )

        self.out(0)
        # None is converted to value with zero validity mask
        # same as self.output._dtype.fromPy(0, vldMask=0)
        self.output(None)

        # statements are code-generator frendly
        stm = \
        Switch(a).Case(1,
            self.sc_signal(0)
        ).Case(2,
           self.sc_signal(1)
        )
        compileTimeCondition = True

        if compileTimeCondition:
            stm.Case(3,
               self.sc_signal(3)
            ).Default(
               self.sc_signal(4)
            )

        # ram working on falling edge of clk
        # note that rams are usually working on rising edge
        fRam = self._sig("fallingEdgeRam", int8_t[4])
        If(self.clk._onFallingEdge(),
           # fit can extend signal and also shrink it
           connect(a, fRam[r1], fit=True),
           connect(fRam[r1]._unsigned(), self.k, fit=True)
        )


showcase0_vhdl = """--
--    Every HW component class has to be derived from Unit class (any kind of inheritance supported)
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY Showcase0 IS
    PORT (a: IN UNSIGNED(31 DOWNTO 0);
        b: IN SIGNED(31 DOWNTO 0);
        c: OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
        clk: IN STD_LOGIC;
        cmp0: OUT STD_LOGIC;
        cmp1: OUT STD_LOGIC;
        cmp2: OUT STD_LOGIC;
        cmp3: OUT STD_LOGIC;
        cmp4: OUT STD_LOGIC;
        cmp5: OUT STD_LOGIC;
        contOut: OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
        d: IN STD_LOGIC_VECTOR(31 DOWNTO 0);
        e: IN STD_LOGIC;
        f: OUT STD_LOGIC;
        fitted: OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
        g: OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        h: OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        i: IN STD_LOGIC_VECTOR(1 DOWNTO 0);
        j: OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        k: OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
        out_0: OUT STD_LOGIC;
        output: OUT STD_LOGIC;
        rst_n: IN STD_LOGIC;
        sc_signal: OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END Showcase0;

ARCHITECTURE rtl OF Showcase0 IS
    TYPE arrT_0 IS ARRAY ((3) DOWNTO 0) OF SIGNED(7 DOWNTO 0);
    TYPE arrT_1 IS ARRAY ((3) DOWNTO 0) OF UNSIGNED(7 DOWNTO 0);
    CONSTANT const_private_signal: UNSIGNED(31 DOWNTO 0) := TO_UNSIGNED(123, 32);
    SIGNAL fallingEdgeRam: arrT_0;
    SIGNAL r: STD_LOGIC := '0';
    SIGNAL r_0: STD_LOGIC_VECTOR(1 DOWNTO 0) := "00";
    SIGNAL r_1: STD_LOGIC_VECTOR(1 DOWNTO 0) := "00";
    SIGNAL r_next: STD_LOGIC;
    SIGNAL r_next_0: STD_LOGIC_VECTOR(1 DOWNTO 0);
    SIGNAL r_next_1: STD_LOGIC_VECTOR(1 DOWNTO 0);
    CONSTANT rom: arrT_1 := (TO_UNSIGNED(0, 8),
        TO_UNSIGNED(1, 8),
        TO_UNSIGNED(2, 8),
        TO_UNSIGNED(3, 8));
BEGIN
    c <= STD_LOGIC_VECTOR(a + UNSIGNED(b));
    cmp0 <= '1' WHEN a < TO_UNSIGNED(4, 32) ELSE '0';
    cmp1 <= '1' WHEN a > TO_UNSIGNED(4, 32) ELSE '0';
    cmp2 <= '1' WHEN b <= TO_SIGNED(4, 32) ELSE '0';
    cmp3 <= '1' WHEN b >= TO_SIGNED(4, 32) ELSE '0';
    cmp4 <= '1' WHEN b /= TO_SIGNED(4, 32) ELSE '0';
    cmp5 <= '1' WHEN b = TO_SIGNED(4, 32) ELSE '0';
    contOut <= STD_LOGIC_VECTOR(const_private_signal);
    f <= r;
    assig_process_fallingEdgeRam: PROCESS (clk)
    BEGIN
        IF FALLING_EDGE(clk) THEN
            fallingEdgeRam(TO_INTEGER(UNSIGNED(r_1))) <= SIGNED(a(7 DOWNTO 0));
            k <= X"000000" & STD_LOGIC_VECTOR(UNSIGNED(fallingEdgeRam(TO_INTEGER(UNSIGNED(r_1)))));
        END IF;
    END PROCESS;

    fitted <= STD_LOGIC_VECTOR(a(15 DOWNTO 0));
    g <= ((a(1)) AND (b(1))) & (((a(0)) XOR (b(0))) OR (a(1))) & STD_LOGIC_VECTOR(a(5 DOWNTO 0));
    assig_process_h: PROCESS (a, r)
    BEGIN
        IF (a(2)) = '1' THEN
            IF r = '1' THEN
                h <= X"00";
            ELSIF (a(1)) = '1' THEN
                h <= X"01";
            ELSE
                h <= X"02";
            END IF;
        END IF;
    END PROCESS;

    assig_process_j: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            j <= STD_LOGIC_VECTOR(rom(TO_INTEGER(UNSIGNED(r_1))));
        END IF;
    END PROCESS;

    out_0 <= '0';
    output <= 'X';
    assig_process_r: PROCESS (clk)
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
    assig_process_r_next_1: PROCESS (e, r)
    BEGIN
        IF (NOT r) = '1' THEN
            r_next <= e;
        ELSE
            r_next <= r;
        END IF;
    END PROCESS;

    assig_process_sc_signal: PROCESS (a)
    BEGIN
        CASE a IS
        WHEN TO_UNSIGNED(1, 32) =>
            sc_signal <= X"00";
        WHEN TO_UNSIGNED(2, 32) =>
            sc_signal <= X"01";
        WHEN TO_UNSIGNED(3, 32) =>
            sc_signal <= X"03";
        WHEN OTHERS =>
            sc_signal <= X"04";
        END CASE;
    END PROCESS;

END ARCHITECTURE rtl;"""

showcase0_verilog = """/*

    Every HW component class has to be derived from Unit class (any kind of inheritance supported)
    
*/
module Showcase0(input [31:0] a,
        input signed [31:0] b,
        output [31:0] c,
        input clk,
        output cmp0,
        output cmp1,
        output cmp2,
        output cmp3,
        output cmp4,
        output cmp5,
        output [31:0] contOut,
        input [31:0] d,
        input e,
        output f,
        output [15:0] fitted,
        output [7:0] g,
        output reg [7:0] h,
        input [1:0] i,
        output reg [7:0] j,
        output reg [31:0] k,
        output out,
        output output_0,
        input rst_n,
        output reg [7:0] sc_signal
    );

    reg [31:0] const_private_signal = 123;
    reg signed [7:0] fallingEdgeRam [4-1:0];
    reg r = 1'b0;
    reg [1:0] r_0 = 2'b00;
    reg [1:0] r_1 = 2'b00;
    reg r_next;
    wire [1:0] r_next_0;
    wire [1:0] r_next_1;
    reg [7:0] rom;
    assign c = a + $unsigned(b);
    assign cmp0 = a < 4;
    assign cmp1 = a > 4;
    assign cmp2 = b <= $signed(4);
    assign cmp3 = b >= $signed(4);
    assign cmp4 = b != $signed(4);
    assign cmp5 = b == $signed(4);
    assign contOut = const_private_signal;
    assign f = r;
    always @(negedge clk) begin: assig_process_fallingEdgeRam
        fallingEdgeRam[r_1] <= $signed(a[7:0]);
        k <= {24'h000000, $unsigned(fallingEdgeRam[r_1])};
    end

    assign fitted = a[15:0];
    assign g = {{(a[1]) & (b[1]), ((a[0]) ^ (b[0])) | (a[1])}, a[5:0]};
    always @(a or r) begin: assig_process_h
        if((a[2])==1'b1) begin
            if((r)==1'b1) begin
                h <= 8'h00;
            end else if((a[1])==1'b1) begin
                h <= 8'h01;
            end else begin
                h <= 8'h02;
            end
        end
    end

    always @(posedge clk) begin: assig_process_j
        j <= rom;
    end

    assign out = 1'b0;
    assign output_0 = 1'bx;
    always @(posedge clk) begin: assig_process_r
        if(rst_n == 1'b0) begin
            r_1 <= 2'b00;
            r_0 <= 2'b00;
            r <= 1'b0;
        end else begin
            r_1 <= r_next_1;
            r_0 <= r_next_0;
            r <= r_next;
        end
    end

    assign r_next_0 = i;
    assign r_next_1 = r_0;
    always @(e or r) begin: assig_process_r_next
        if((~r)==1'b1) begin
            r_next <= e;
        end else begin
            r_next <= r;
        end
    end

    always @(a) begin: assig_process_sc_signal
        case(a)
        1:
            sc_signal <= 8'h00;
        2:
            sc_signal <= 8'h01;
        3:
            sc_signal <= 8'h03;
        default:
            sc_signal <= 8'h04;
        endcase
    end

    always @(r_1) begin: rom_0
        case(r_1)
        0:
            rom <= 0;
        1:
            rom <= 1;
        2:
            rom <= 2;
        3:
            rom <= 3;
        endcase
    end

endmodule"""

showcase0_systemc = """/*

    Every HW component class has to be derived from Unit class (any kind of inheritance supported)
    
*/

#include <systemc.h>


SC_MODULE(Showcase0) {
    //interfaces
    sc_in<sc_uint<32>> a;
    sc_in<sc_int<32>> b;
    sc_out<sc_uint<32>> c;
    sc_in_clk clk;
    sc_out<sc_uint<1>> cmp0;
    sc_out<sc_uint<1>> cmp1;
    sc_out<sc_uint<1>> cmp2;
    sc_out<sc_uint<1>> cmp3;
    sc_out<sc_uint<1>> cmp4;
    sc_out<sc_uint<1>> cmp5;
    sc_out<sc_uint<32>> contOut;
    sc_in<sc_uint<32>> d;
    sc_in<sc_uint<1>> e;
    sc_out<sc_uint<1>> f;
    sc_out<sc_uint<16>> fitted;
    sc_out<sc_uint<8>> g;
    sc_out<sc_uint<8>> h;
    sc_in<sc_uint<2>> i;
    sc_out<sc_uint<8>> j;
    sc_out<sc_uint<32>> k;
    sc_out<sc_uint<1>> out;
    sc_out<sc_uint<1>> output;
    sc_in<sc_uint<1>> rst_n;
    sc_out<sc_uint<8>> sc_signal_0;

    //internal signals
    sc_uint<32> const_private_signal = sc_biguint<32>(123);
    sc_int<8> fallingEdgeRam [4];
    sc_uint<1> r = '0';
    sc_uint<2> r_0 = sc_uint<2>("00");
    sc_uint<2> r_1 = sc_uint<2>("00");
    sc_signal<sc_uint<1>> r_next;
    sc_signal<sc_uint<2>> r_next_0;
    sc_signal<sc_uint<2>> r_next_1;
    sc_uint<8> rom [4] = {sc_biguint<8>(0),
        sc_biguint<8>(1),
        sc_biguint<8>(2),
        sc_biguint<8>(3)};

    //processes inside this component
    void assig_process_c() {
        c.write(static_cast<sc_uint<32>>(a.read() + static_cast<sc_uint<32>>(b.read())));
    }
    void assig_process_cmp0() {
        cmp0.write(a.read() < sc_biguint<32>(4));
    }
    void assig_process_cmp1() {
        cmp1.write(a.read() > sc_biguint<32>(4));
    }
    void assig_process_cmp2() {
        cmp2.write(b.read() <= sc_biguint<32>(4));
    }
    void assig_process_cmp3() {
        cmp3.write(b.read() >= sc_biguint<32>(4));
    }
    void assig_process_cmp4() {
        cmp4.write(b.read() != sc_biguint<32>(4));
    }
    void assig_process_cmp5() {
        cmp5.write(b.read() == sc_biguint<32>(4));
    }
    void assig_process_contOut() {
        contOut.write(static_cast<sc_uint<32>>(const_private_signal));
    }
    void assig_process_f() {
        f.write(r);
    }
    void assig_process_fallingEdgeRam() {
        fallingEdgeRam[r_1] = static_cast<sc_int<8>>(a.read().range(8, 0));
        k = sc_uint<24>("0x000000") & static_cast<sc_uint<8>>(static_cast<sc_uint<8>>(fallingEdgeRam[r_1]));
    }
    void assig_process_fitted() {
        fitted.write(static_cast<sc_uint<16>>(a.read().range(16, 0)));
    }
    void assig_process_g() {
        g.write((a.read()[1]) & (b.read()[1]) & ((a.read()[0]) ^ (b.read()[0])) | (a.read()[1]) & static_cast<sc_uint<6>>(a.read().range(6, 0)));
    }
    void assig_process_h() {
        if((a.read()[2]) == '1') {
            if(r == '1') {
                h.write(sc_uint<8>("0x00"));
            } else if((a.read()[1]) == '1') {
                h.write(sc_uint<8>("0x01"));
            } else {
                h.write(sc_uint<8>("0x02"));
            }
        }
    }
    void assig_process_j() {
        j = static_cast<sc_uint<8>>(rom[r_1]);
    }
    void assig_process_out() {
        out.write('0');
    }
    void assig_process_output() {
        output.write('X');
    }
    void assig_process_r() {
        if(rst_n.read() == '0') {
            r_1 = sc_uint<2>("00");
            r_0 = sc_uint<2>("00");
            r = '0';
        } else {
            r_1 = r_next_1.read();
            r_0 = r_next_0.read();
            r = r_next.read();
        }
    }
    void assig_process_r_next() {
        r_next_0.write(i.read());
    }
    void assig_process_r_next_0() {
        r_next_1.write(r_0);
    }
    void assig_process_r_next_1() {
        if((~r) == '1') {
            r_next.write(e.read());
        } else {
            r_next.write(r);
        }
    }
    void assig_process_sc_signal() {
        switch(a.read()) {
        case sc_biguint<32>(1):
            sc_signal_0.write(sc_uint<8>("0x00"));
            break;
        case sc_biguint<32>(2):
            sc_signal_0.write(sc_uint<8>("0x01"));
            break;
        case sc_biguint<32>(3):
            sc_signal_0.write(sc_uint<8>("0x03"));
            break;
        default:
            sc_signal_0.write(sc_uint<8>("0x04"));
            break;
        }
    }

    SC_CTOR(Showcase0) {
        SC_METHOD(assig_process_c);
        sensitive << a << b;
        SC_METHOD(assig_process_cmp0);
        sensitive << a;
        SC_METHOD(assig_process_cmp1);
        sensitive << a;
        SC_METHOD(assig_process_cmp2);
        sensitive << b;
        SC_METHOD(assig_process_cmp3);
        sensitive << b;
        SC_METHOD(assig_process_cmp4);
        sensitive << b;
        SC_METHOD(assig_process_cmp5);
        sensitive << b;
        SC_METHOD(assig_process_contOut);
        
        SC_METHOD(assig_process_f);
        sensitive << r;
        SC_METHOD(assig_process_fallingEdgeRam);
        sensitive << clk.neg();
        SC_METHOD(assig_process_fitted);
        sensitive << a;
        SC_METHOD(assig_process_g);
        sensitive << a << b;
        SC_METHOD(assig_process_h);
        sensitive << a << r;
        SC_METHOD(assig_process_j);
        sensitive << clk.pos();
        SC_METHOD(assig_process_out);
        
        SC_METHOD(assig_process_output);
        
        SC_METHOD(assig_process_r);
        sensitive << clk.pos();
        SC_METHOD(assig_process_r_next);
        sensitive << i;
        SC_METHOD(assig_process_r_next_0);
        sensitive << r_0;
        SC_METHOD(assig_process_r_next_1);
        sensitive << e << r;
        SC_METHOD(assig_process_sc_signal);
        sensitive << a;
    }
};"""

showcase0_hwt = """from hwt.code import power, If, Concat
from hwt.hdl.types.array import HArray
from hwt.hdl.types.arrayVal import HArrayVal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import INT, SLICE
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.integerVal import SliceVal
from hwt.interfaces.std import Signal
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class Showcase0(Unit):

    def _declr(self):
        self.a = Signal(dtype=Bits(32, signed=False))
        self.b = Signal(dtype=Bits(32, signed=True))
        self.c = Signal(dtype=Bits(32))
        self.clk = Signal(dtype=Bits(1))
        self.cmp0 = Signal(dtype=Bits(1))
        self.cmp1 = Signal(dtype=Bits(1))
        self.cmp2 = Signal(dtype=Bits(1))
        self.cmp3 = Signal(dtype=Bits(1))
        self.cmp4 = Signal(dtype=Bits(1))
        self.cmp5 = Signal(dtype=Bits(1))
        self.contOut = Signal(dtype=Bits(32, forceVector=True))
        self.d = Signal(dtype=Bits(32, forceVector=True))
        self.e = Signal(dtype=Bits(1))
        self.f = Signal(dtype=Bits(1))
        self.fitted = Signal(dtype=Bits(16, forceVector=True))
        self.g = Signal(dtype=Bits(8, forceVector=True))
        self.h = Signal(dtype=Bits(8, forceVector=True))
        self.i = Signal(dtype=Bits(2, forceVector=True))
        self.j = Signal(dtype=Bits(8, forceVector=True))
        self.k = Signal(dtype=Bits(32, forceVector=True))
        self.out = Signal(dtype=Bits(1))
        self.output = Signal(dtype=Bits(1))
        self.rst_n = Signal(dtype=Bits(1, negated=True))
        self.sc_signal = Signal(dtype=Bits(8, forceVector=True))

    def _impl(self):
        a, b, c, clk, cmp0, cmp1, cmp2, cmp3, cmp4, cmp5, contOut, d, e, f, fitted, g, h, i, j, k, out, output, rst_n, sc_signal = self.a, self.b, self.c, self.clk, self.cmp0, self.cmp1, self.cmp2, self.cmp3, self.cmp4, self.cmp5, self.contOut, self.d, self.e, self.f, self.fitted, self.g, self.h, self.i, self.j, self.k, self.out, self.output, self.rst_n, self.sc_signal
        # constants 
        const_0_0 = None
        # internal signals
        const_private_signal = self._sig("const_private_signal", Bits(32, signed=False), defVal=0x7b)
        fallingEdgeRam = self._sig("fallingEdgeRam", HArray(Bits(8, signed=True), 4), defVal=None)
        r = self._sig("r", Bits(1), defVal=0x0)
        r_0 = self._sig("r_0", Bits(2), defVal=0x0)
        r_1 = self._sig("r_1", Bits(2), defVal=0x0)
        r_next = self._sig("r_next", Bits(1), defVal=None)
        r_next_0 = self._sig("r_next_0", Bits(2), defVal=None)
        r_next_1 = self._sig("r_next_1", Bits(2), defVal=None)
        rom = self._sig("rom", HArray(Bits(8, signed=False), 4), defVal={0: 0x0,
            1: 0x1,
            2: 0x2,
            3: 0x3})
        # assig_process_c sensitivity: a, b
        c((a + (b)._reinterpret_cast(Bits(32, signed=False)))._reinterpret_cast(Bits(32)))
        # assig_process_cmp0 sensitivity: a
        cmp0((a < 0x4)._ternary(Bits(1).fromPy(0x1), Bits(1).fromPy(0x0)))
        # assig_process_cmp1 sensitivity: a
        cmp1((a > 0x4)._ternary(Bits(1).fromPy(0x1), Bits(1).fromPy(0x0)))
        # assig_process_cmp2 sensitivity: b
        cmp2((b <= 0x4)._ternary(Bits(1).fromPy(0x1), Bits(1).fromPy(0x0)))
        # assig_process_cmp3 sensitivity: b
        cmp3((b >= 0x4)._ternary(Bits(1).fromPy(0x1), Bits(1).fromPy(0x0)))
        # assig_process_cmp4 sensitivity: b
        cmp4((b != 0x4)._ternary(Bits(1).fromPy(0x1), Bits(1).fromPy(0x0)))
        # assig_process_cmp5 sensitivity: b
        cmp5((b._eq(0x4))._ternary(Bits(1).fromPy(0x1), Bits(1).fromPy(0x0)))
        # assig_process_contOut sensitivity: 
        contOut((const_private_signal)._reinterpret_cast(Bits(32)))
        # assig_process_f sensitivity: r
        f(r)
        # assig_process_fallingEdgeRam sensitivity: (SENSITIVITY.FALLING, clk)
        If((clk)._onFallingEdge(),
            fallingEdgeRam[(r_1)._reinterpret_cast(INT)](((a)[8:0])._reinterpret_cast(Bits(8, signed=True, forceVector=True))),
            k(Concat(Bits(24, forceVector=True).fromPy(0x0), (((fallingEdgeRam)[(r_1)._reinterpret_cast(INT)])._reinterpret_cast(Bits(8, signed=False)))._reinterpret_cast(Bits(8)))),
        )
        # assig_process_fitted sensitivity: a
        fitted(((a)[16:0])._reinterpret_cast(Bits(16, forceVector=True)))
        # assig_process_g sensitivity: a, b
        g(Concat(Concat(((a)[1]) & ((b)[1]), (((a)[0]) ^ ((b)[0])) | ((a)[1])), ((a)[6:0])._reinterpret_cast(Bits(6, forceVector=True))))
        # assig_process_h sensitivity: a, r
        If((a)[2],
            If(r,
                h(0x0),
            ).Elif((a)[1],
                h(0x1),
            ).Else(
                h(0x2),
            ),
        )
        # assig_process_j sensitivity: (SENSITIVITY.RISING, clk)
        If((clk)._onRisingEdge(),
            j(((rom)[(r_1)._reinterpret_cast(INT)])._reinterpret_cast(Bits(8))),
        )
        # assig_process_out sensitivity: 
        out(0x0)
        # assig_process_output sensitivity: 
        output(const_0_0)
        # assig_process_r sensitivity: (SENSITIVITY.RISING, clk)
        If((clk)._onRisingEdge(),
            If(rst_n._eq(0x0),
                r_1(0x0),
                r_0(0x0),
                r(0x0),
            ).Else(
                r_1(r_next_1),
                r_0(r_next_0),
                r(r_next),
            ),
        )
        # assig_process_r_next sensitivity: i
        r_next_0(i)
        # assig_process_r_next_0 sensitivity: r_0
        r_next_1(r_0)
        # assig_process_r_next_1 sensitivity: e, r
        If(~r,
            r_next(e),
        ).Else(
            r_next(r),
        )
        # assig_process_sc_signal sensitivity: a
        If(a._eq(0x1),
            sc_signal(0x0),
        ).Elif(a._eq(0x2),
            sc_signal(0x1),
        ).Elif(a._eq(0x3),
            sc_signal(0x3),
        ).Else(
            sc_signal(0x4),
        )"""

if __name__ == "__main__":  # alias python main function
    from pprint import pprint

    from hwt.synthesizer.utils import toRtl
    from hwt.serializer.hwt.serializer import HwtSerializer
    from hwt.serializer.vhdl.serializer import VhdlSerializer
    from hwt.serializer.verilog.serializer import VerilogSerializer
    from hwt.serializer.systemC.serializer import SystemCSerializer
    # from hwt.serializer.simModel.serializer import SimModelSerializer
    from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer

    # * new instance has to be created every time because toRtl is modifies the unit
    # * serializers are using templates which can be customized
    # serialized code is trying to be human and git friednly
    print(toRtl(Showcase0(), serializer=HwtSerializer))
    print(toRtl(Showcase0(), serializer=VhdlSerializer))
    print(toRtl(Showcase0(), serializer=VerilogSerializer))
    print(toRtl(Showcase0(), serializer=SystemCSerializer))
    #print(toRtl(Showcase0(), serializer=SimModelSerializer))

    #r = ResourceAnalyzer()
    #print(toRtl(Showcase0(), serializer=r))
    #pprint(r.report())
