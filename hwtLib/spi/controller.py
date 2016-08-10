from math import log2

from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hBit
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.interfaces.spi import SPI
from hdl_toolkit.interfaces.std import VldSynced, Signal
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.utils import isPow2
from hdl_toolkit.synthesizer.codeOps import c, Switch, If, FsmBuilder
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam


class SPICntrlW(Unit):
    # https://github.com/medons/Zedboard_OLED_Example/blob/master/SpiCtrl.vhd
    def _config(self):
        self.SPI_FREQ_PESCALER = Param(32)
        
    def _declr(self):
        with self._asExtern(): 
            addClkRstn(self)
            self.dataIn = VldSynced()
            self.dataIn.DATA_WIDTH.set(8)
            self.dataOut = SPI() 
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
        c(clk_divided, Out.clk)
        
        c(mosiReg, Out.mosi)
        c(st._eq(stT.idle) & In.vld, Out.cs)
        c(st._eq(stT.done), self.dataInDone)
        
        # CLK_DIV
        If(st._eq(stT.send),  # start clock counter when in send state
           c(delayCntr + 1, delayCntr)
        ).Else(# reset clock counter when not in send state
           c(0, delayCntr)
        )
        
        If(st._eq(stT.send),
            If(clk_divided,
                c(0, falling)
            ).Elif(~falling,
                c(1, falling),  # Indicate that it is passed the falling edge
            ).Else(
                falling._same()
            )
        ).Else(
            falling._same()
        )
        def dataShiftNop():
            return (shift_register._same() + 
                    shift_counter._same() + 
                    mosiReg._same()
                   )

        # SPI_SEND_BYTE
        # sends SPI data formatted SCLK active low with SDO changing on the falling edge
        Switch(st)\
        .Case(stT.idle,
            c(0, shift_counter),
            # keeps placing SPI_DATA into shift_register so that when state goes 
            # to send it has the latest SPI_DATA
            c(In.data, shift_register),
            c(1, mosiReg)
        ).Case(stT.send,
            If(~clk_divided & ~falling,  # if on the falling edge of Clk_divided
                c(shift_register[7], mosiReg),  # send out the MSB
                c(shift_register[7:0]._concat(hBit(0)), shift_register),
                c(shift_counter + 1, shift_counter)  
            ).Else(
                dataShiftNop()
            )
        ).Default(
            dataShiftNop()
        )
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = SPICntrlW()
    print(toRtl(u))
