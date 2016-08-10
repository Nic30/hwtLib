import hwtLib.proc.ssd1306cntrl.instructions as instrSet
from hdl_toolkit.synthesizer.codeOps import If, c, Switch, In
from hdl_toolkit.hdlObjects.types.array import Array
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hwtLib.img.charToBitmap import addCharToBitmap

class SSD1306CntrlProc_handlers():
    """
    Handlers of procesor resources
    """
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
