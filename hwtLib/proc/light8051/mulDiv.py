#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT, hBit, vec
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import If, c, Concat, sll, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param


class MulDiv(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
    def _declr(self):
        word_t = vecT(self.DATA_WIDTH)
        addClkRstn(self)
        # Numerator input, should be connected to the ACC register.
        self.data_a = Signal(dtype=word_t)
        
        # Denominator input, should be connected to the B register.
        self.data_b = Signal(dtype=word_t)
        
        self.start = Signal()
        
        # Product output, valid only when mul_ready='1'.
        self.prod_out = Signal(dtype=vecT(self.DATA_WIDTH * 2))
        
        # Quotient output, valid only when div_ready='1'.
        self.quot_out = Signal(dtype=word_t)
        
        # Remainder output, valid only when div_ready='1'.
        self.rem_out = Signal(dtype=word_t)
        
        # Division overflow flag, valid only when div_ready='1'.
        self.div_ov_out = Signal()
        
        # Product overflow flag, valid only when mul_ready='1'.
        self.mul_ov_out = Signal()
        
        
        self.mul_ready = Signal()
        
        # Asserted when the division has completed.
        self.div_ready = Signal()
    
    def divPart(self):
        """
        What we do is a simple base-2 'shift-and-subtract' algorithm that takes
        8 cycles to complete. We can get away with this because we deal with unsigned
        numbers only.
        """
        DW = self.DATA_WIDTH
        bit_cntr = self._reg("bit_ctr", vecT(log2ceil(DW + 1)),
                         defVal=DW)
        b_shift_reg = self._reg("b_shift_reg", vecT(DW * 2))
        div_ov_out = self._reg("div_ov_out_reg")
        c(div_ov_out, self.div_ov_out)
        rem_reg = self._reg("rem_reg", vecT(DW))
        quot_reg = self._reg("quot_reg", vecT(DW))
        
        denominator = b_shift_reg[DW:];
        # The 16-bit comparison between b_shift_reg (denominator) and the zero-extended 
        # rem_reg (numerator) can be simplified by splitting it in 2: 
        # If the shifted denominator high byte is not zero, it is >=256...
        den_ge_256 = b_shift_reg[:DW] != 0
        # ...otherwise we need to compare the low bytes.
        num_ge_den = rem_reg >= denominator
         
        sub_num = self._sig("sub_num")
        sub_num ** (~den_ge_256 & num_ge_den)
        
        If(self.start,
           bit_cntr ** 0 
        ).Elif(bit_cntr != DW,
            bit_cntr ** (bit_cntr + 1)
        )
        # denominator shift register
        If(self.start,
           b_shift_reg ** Concat(hBit(0), self.data_b, vec(0, DW - 1)),
           div_ov_out ** (self.data_b != 0)
        ).Else(
           b_shift_reg ** sll(b_shift_reg, 1) 
        )
        # numerator register
        If(self.start,
            rem_reg ** self.data_a
        ).Elif((bit_cntr != DW) & sub_num,
            rem_reg ** (rem_reg - denominator)
        )
        #  quotient register
        If(self.start,
            quot_reg ** 0 
        ).Elif(bit_cntr != DW,
            quot_reg ** quot_reg[DW - 1:]._concat(sub_num) 
        )
        self.div_ready ** bit_cntr._eq(8)
        self.quot_out ** quot_reg
        self.rem_out ** rem_reg
    
    def mulPart(self):
        DW = self.DATA_WIDTH
        # The multiplier output is valid in the cycle after the operands are loaded,
        # so by the time MUL is executed it's already done.

        c(1, self.mul_ready)
        prod_reg = self._reg("prod_reg", vecT(DW * 2))
        prod_reg ** (self.data_a * self.data_b)
        
        self.prod_out ** prod_reg
        self.mul_ov_out ** (prod_reg[:DW] != 0)
        
        
    def _impl(self):
        self.divPart()
        self.mulPart()
        

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(MulDiv()))
    
