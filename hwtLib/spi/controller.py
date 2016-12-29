#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import log2

from hwt.hdlObjects.typeShortcuts import vecT, hBit
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import VldSynced, Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import Switch, If, FsmBuilder, isPow2
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.interfaces.peripheral import Spi


class SPICntrlW(Unit):
    # https://github.com/medons/Zedboard_OLED_Example/blob/master/SpiCtrl.vhd
    def _config(self):
        self.SPI_FREQ_PESCALER = Param(32)
        
    def _declr(self):
        addClkRstn(self)
        self.dataIn = VldSynced()
        self.dataIn.DATA_WIDTH.set(8)
        self.dataOut = Spi() 
        self.dataInDone = Signal()
            
    
    def mainFsm(self, shift_counter, falling):
        stT = Enum("st_t", ["idle",
                            "send",
                            "hold1",
                            "hold2",
                            "hold3",
                            "hold4",
                            "done"])
        
        In = self.dataIn.vld
        
        
        stb = FsmBuilder(self, stT)\
        .Trans(stT.idle,
                   # Wait for SPI_EN to go high 
                   (In, stT.send)
        ).Trans(stT.send,
                # Start sending bits, transition out when all bits are sent and SCLK is high
                (shift_counter._eq(0b1000) & ~falling,
                                                      stT.hold1)
        ).Trans(stT.hold1,  # Hold CS low for a bit
            stT.hold2
        ).Trans(stT.hold2,  # Hold CS low for a bit
            stT.hold3
        ).Trans(stT.hold3,  # Hold CS low for a bit
            stT.hold4
        ).Trans(stT.hold4,  # Hold CS low for a bit
            stT.done
        ).Default(# stT.done,   Finish SPI transmission wait for SPI_EN to go low
            (~In,
                stT.idle
            )
        )
        return stb.stateReg
    
    def _impl(self):
        presc = evalParam(self.SPI_FREQ_PESCALER).val
        assert isPow2(presc)
        delayShiftCntrBits = int(log2(presc))
        Out = self.dataOut
        In = self.dataIn
        
        shift_counter = self._reg("shift_counter", vecT(4))
        falling = self._reg("falling", defVal=0)
        shift_register = self._reg("shift_register", In.data._dtype)
        delayCntr = self._reg("delayCntr", vecT(delayShiftCntrBits), defVal=0)
        mosiReg = self._reg("mosiReg", defVal=1)
        

        st = self.mainFsm(shift_counter, falling)
        stT = st._dtype
        # shift_register = self._reg
        
        clk_divided = ~delayCntr[delayShiftCntrBits - 1]
        Out.clk ** clk_divided
        
        Out.mosi ** mosiReg
        Out.cs ** (st._eq(stT.idle) & In.vld)
        self.dataInDone ** st._eq(stT.done)
        
        # CLK_DIV
        If(st._eq(stT.send),  # start clock counter when in send state
           delayCntr ** (delayCntr + 1)
        ).Else(# reset clock counter when not in send state
           delayCntr ** 0
        )
        
        If(st._eq(stT.send),
            If(clk_divided,
                falling ** 0 
            ).Elif(~falling,
                falling ** 1,  # Indicate that it is passed the falling edge
            )
        )

        # SPI_SEND_BYTE
        # sends SPI data formatted SCLK active low with SDO changing on the falling edge
        Switch(st)\
        .Case(stT.idle,
            shift_counter ** 0 ,
            # keeps placing SPI_DATA into shift_register so that when state goes 
            # to send it has the latest SPI_DATA
            shift_register ** In.data ,
            mosiReg ** 1
        ).Case(stT.send,
            If(~clk_divided & ~falling,  # if on the falling edge of Clk_divided
                mosiReg ** shift_register[7],  # send out the MSB
                shift_register ** shift_register[7:0]._concat(hBit(0)),
                shift_counter ** (shift_counter + 1)  
            )
        )
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = SPICntrlW()
    print(toRtl(u))
