#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.code import FsmBuilder, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.logic.delayMs import DelayMs
from hwtLib.proc.ssd1306cntrl.handlers import SSD1306CntrlProc_handlers
import hwtLib.proc.ssd1306cntrl.instructions as instrSet
from hwtLib.proc.ssd1306cntrl.interfaces import Ssd1306Intf
from hwtLib.spi.controller import SPICntrlW
from hwtLib.types.ctypes import char


class SSD1306CntrlProc(Unit, SSD1306CntrlProc_handlers):
    """
    SSD1306 contrller processor
    
    This proc. can initialize lcd and print ascii values from dataIn.
    
    Instruction set is described in "instructions" modle.
    "code" module contains code examples
    """
    def _config(self):
        self.MEM_SIZE = Param(64)
        self.FREQ = Param(int(100e6)) 
        self.PROGRAM = []
        
    def _declr(self):
        addClkRstn(self)
        self.oled = Ssd1306Intf()
        
        self.dataIn = Handshaked()
        self.dataIn.DATA_WIDTH.set(8)
        
        with self._paramsShared():
            self.delay = DelayMs()
        # [TODO] clk prescaler always should be 33mhz
        self.spiCntrl = SPICntrlW()
        
        self.COLUMNS = Param(16)
        self.ROWS = Param(3) 
        
    def mainFsm(self, ir, delayDone, spiDone):
        # main fsm state
        stT = Enum("stT", [
            "load",
            "decode",
                "NOP",
                "PIN_SET",
                
                "LOAD_DATA",
                "LOAD_DATA_collectAndIncr",
                
                "LOAD_ROW",
                
                "LOAD_BM_ROW",
                "LOAD_BM_ROW_collect",
                
                "LOAD_EXTERN",
                
                "DO_WAIT",
                "DO_WAIT_wait",
                "DO_WAIT_off",
                
                "SEND",
                "SEND_wait",
                "SEND_spi_off",
                
                "STORE_CHAR",
                "COLUMN_INCR",
                "COLUMN_CLR",
                "ROW_INCR",
                "ROW_CLR",
            "incr_IP"
        ])
        end = stT.incr_IP

        def instrExe(instrState):
            """
            Shortcut for fsm generetor
            if instr is in ir generate transition
            """
            instrName = instrState.val
            instrCode = getattr(instrSet, instrName)
            
            return ir[4:0]._eq(instrCode), instrState
        
        # generate main fsm
        fsmb = FsmBuilder(self, stT)
        fsmb = fsmb\
        .Trans(stT.load,  # load instruction pointer from mem[IP]
               stT.decode
        
        # instruction pointer decode
        ).Trans(stT.decode,
            instrExe(stT.PIN_SET),
            instrExe(stT.LOAD_DATA),
            instrExe(stT.LOAD_ROW),
            instrExe(stT.LOAD_BM_ROW),
            instrExe(stT.LOAD_EXTERN),
            instrExe(stT.DO_WAIT),
            instrExe(stT.SEND),
            instrExe(stT.STORE_CHAR),
            instrExe(stT.COLUMN_INCR),
            instrExe(stT.COLUMN_CLR),
            instrExe(stT.ROW_INCR),
            instrExe(stT.ROW_CLR),
            stT.NOP
        
        # load data from memory behind instr pointer
        ).Trans(stT.LOAD_DATA,
            stT.LOAD_DATA_collectAndIncr
        ).Trans(stT.LOAD_DATA_collectAndIncr,
            end
        
        ).Trans(stT.LOAD_BM_ROW,
            stT.LOAD_BM_ROW_collect
        
        # wait while exter data is recieved
        ).Trans(stT.LOAD_EXTERN,
            (self.dataIn.vld, end)
        
        # delay
        ).Trans(stT.DO_WAIT,
            stT.DO_WAIT_wait
        ).Trans(stT.DO_WAIT_wait,
            (delayDone, stT.DO_WAIT_off)
        
        # send
        ).Trans(stT.SEND,
            stT.SEND_wait
        ).Trans(stT.SEND_wait,
            (spiDone, stT.SEND_spi_off)
            
        # instr pointer increment
        ).Trans(stT.incr_IP,
            stT.load
        )

        
        # add states which are falling to incr_ip immediately        
        singleClkInstr = [stT.PIN_SET, stT.LOAD_ROW, stT.STORE_CHAR, stT.COLUMN_INCR, stT.COLUMN_CLR,
                          stT.ROW_INCR, stT.ROW_CLR, stT.NOP, stT.SEND_spi_off, stT.DO_WAIT_off, ]
        
        for i in singleClkInstr:
            fsmb = fsmb.Trans(i, stT.incr_IP)  
        fsmb.Default(
            stT.load
        )
        
        return fsmb.stateReg
    
           
    def _impl(self):
        assert self.PROGRAM  # do not forget to asign code to this processor
        
        propagateClkRstn(self)
        
        ADDR_W = log2ceil(self.MEM_SIZE) 
        ir = self._reg("instruction_reg", vecT(8))
        ip = self._reg("instruction_pointer_reg", vecT(ADDR_W), 0)
        acc = self._reg("accumulator_reg", vecT(8))
        vdd = self._reg("vdd_reg", defVal=1)
        vbat = self._reg("vbat_reg", defVal=1)
        res = self._reg("res_reg", defVal=1)
        dc = self._reg("dc_reg", defVal=0)
        column = self._reg("column_reg", vecT(log2ceil(self.COLUMNS - 1)))
        row = self._reg("row_reg", vecT(log2ceil(self.ROWS - 1)))
        charTmp = self._reg("charTmp_reg", char)
        

        st = self.mainFsm(ir, self.delay.acivate.done, self.spiCntrl.dataInDone)
        memData = self.memHandler(st, ip)

        self.pinsHandler(st, ir, vdd, vbat, res, dc)
        self.dellayHandler(st, acc)
        self.sendHandler(st, acc)
        self.columnHandler(st, column)
        self.rowHandler(st, row)
        self.charRegHandler(st, acc, charTmp)
        charBmRow = self.bmMapHandler(st)
        self.accHandler(st, memData, charBmRow, acc)
        self.irHandler(st, memData, ir)
        self.ipHandler(st, ip)
        
        self.dataIn.rd ** st._eq(st._dtype.LOAD_EXTERN) 
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.proc.ssd1306cntrl.code import simpleCodeExample
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = SSD1306CntrlProc()
    u.PROGRAM = simpleCodeExample
    print(toRtl(u))
