from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hdl_toolkit.synthetisator.interfaceLevel.interface import Interface
from hdl_toolkit.interfaces.spi import SPI
from hdl_toolkit.interfaces.std import Signal, Handshaked
from hdl_toolkit.hdlObjects.types.enum import Enum

from hdl_toolkit.synthetisator.codeOps import c, Switch, If, In, FsmBuilder, \
    fitTo
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.param import Param

from hwtLib.spi.controller import SPICntrlW
from hwtLib.logic.delayMs import DelayMs
from hwtLib.img.charToBitmap import addCharToBitmap
import hwtLib.proc.ssd1306Cntrl_instr as instrSet
from hwtLib.types.ctypes import char
from hdl_toolkit.hdlObjects.types.array import Array
from hwtLib.proc.ssd1306CntrlProcessor_code import simpleCodeExample

class OledIntf(Interface):
    def _config(self):
        DelayMs._config(self)
    
    def _declr(self):
        self.spi = SPI()
        self.dc = Signal()  # Data/Command Pin
        self.res = Signal()  # PmodOLED RES
        self.vbat = Signal()  # VBAT enable
        self.vdd = Signal()  # VDD enable
 
class SSD1306CntrlProc(Unit):
    def _config(self):
        self.MEM_SIZE = Param(64)
        self.FREQ = Param(int(100e6)) 
        self.PROGRAM = []
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.oled = OledIntf()
            
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
    
    def pinsHandler(self, st, ir, vdd, vbat, res, dc):
        selPin = ir[7:4]
        allPins = [vdd, vbat, res, dc]
        allPinCodes = [instrSet.PIN_VDD, instrSet.PIN_VBAT, instrSet.PIN_RES, instrSet.PIN_DC]
    
        val = ir[7]
        for pin, _pinCode in zip(allPins, allPinCodes):
            If(st._eq(st._dtype.PIN_SET) & selPin._eq(_pinCode),
                c(val, pin)
            ).Else(
                pin._same()
            )
        

        c(vdd, self.oled.vdd)
        c(vbat, self.oled.vbat)
        c(res, self.oled.res)
        c(dc, self.oled.dc)
    
    def dellayHandler(self, st, acc):
        stT = st._dtype

        c(acc[7:], self.delay.delayTime)
        c(st._eq(stT.DO_WAIT) | st._eq(stT.DO_WAIT_wait), self.delay.acivate.req)
        
    def sendHandler(self, st, acc):
        stT = st._dtype

        c(acc, self.spiCntrl.dataIn.data)
        c(st._eq(stT.SEND) | st._eq(stT.SEND_wait), self.spiCntrl.dataIn.vld)
        
        c(self.spiCntrl.dataOut, self.oled.spi)
    
    def columnHandler(self, st, column):
        stT = st._dtype
        Switch(st)\
        .Case(stT.COLUMN_INCR,
            If(column._eq(self.COLUMNS - 1),
                c(0, column)
            ).Else(
                c(column + 1, column)
            )
        ).Case(stT.COLUMN_CLR,
            c(0, column)
        ).Default(
            column._same()
        )
        
    def rowHandler(self, st, row):
        stT = st._dtype
        Switch(st)\
        .Case(stT.ROW_INCR,
            If(row._eq(self.ROWS - 1),
                c(0, row)
            ).Else(
                c(row + 1, row)
            )
        ).Case(stT.ROW_CLR,
            c(0, row)
        ).Default(
            row._same()
        )
        
    def charRegHandler(self, st, acc, charReg):
        If(st._eq(st._dtype.STORE_CHAR),
            c(acc, charReg)
        ).Else(
            charReg._same()
        )
        
    def accHandler(self, st, charBmRow, memData, acc):
        stT = st._dtype

        Switch(st)\
        .Case(stT.LOAD_DATA_collectAndIncr,
            c(memData, acc)
        ).Case(stT.LOAD_BM_ROW_collect,
            c(charBmRow, acc)
        ).Case(stT.LOAD_EXTERN,
            c(self.dataIn.data, acc)
        ).Default(
            acc._same()
        )

    def irHandler(self, st, memData, ir):
        If(st._eq(st._dtype.load),
           c(memData, ir)
        ).Else(
           ir._same()
        )
    
    def ipHandler(self, st, ip):
        stT = st._dtype
        If(In(st, [stT.incr_IP, stT.LOAD_DATA_collectAndIncr]),
           c(ip + 1, ip)
        ).Else(
           ip._same()
        )
    
    def memHandler(self, st, ip):
        mem = self._sig("mem", Array(vecT(8), len(self.PROGRAM)), defVal=self.PROGRAM)
        memData = self._sig("memData", vecT(8))
        stT = st._dtype 
        
        If(self.clk._onRisingEdge(),
            If(In(st, [stT.LOAD_DATA, stT.LOAD_DATA_collectAndIncr]),
                c(mem[ip + 1], memData)
            ).Else(
                c(mem[ip], memData)
            )
        )
        return memData
    
    def bmMapHandler(self, st):
        charToBitmap = addCharToBitmap(self)
        charBmRow = self._sig("charBmRow", vecT(8))
        charBmRowAddr = self._reg("charBmRowAddr", vecT(8), defVal=0)
        
        If(self.clk._onRisingEdge(),
           c(charToBitmap[charBmRowAddr], charBmRow)
        )
        If(st._eq(st._dtype.LOAD_BM_ROW_collect),
            c(charBmRowAddr + 1, charBmRowAddr)
        ).Else(
            charBmRowAddr._same()
        )
        return charBmRow
           
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
        
        c(st._eq(st._dtype.LOAD_EXTERN), self.dataIn.rd)
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = SSD1306CntrlProc()
    u.PROGRAM = simpleCodeExample
    print(toRtl(u))
