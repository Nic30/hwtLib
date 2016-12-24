import hwtLib.proc.ssd1306cntrl.instructions as instrSet
from hwt.code import If, Switch, In
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.typeShortcuts import vecT
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
                pin ** val
            )        
    
        self.oled.vdd ** vdd
        self.oled.vbat ** vbat 
        self.oled.res ** res 
        self.oled.dc ** dc 
    
    def dellayHandler(self, st, acc):
        stT = st._dtype
    
        self.delay.delayTime ** acc[7:]
        self.delay.acivate.req ** (st._eq(stT.DO_WAIT) | st._eq(stT.DO_WAIT_wait))
        
    def sendHandler(self, st, acc):
        stT = st._dtype
    
        self.spiCntrl.dataIn.data ** acc
        self.spiCntrl.dataIn.vld ** (st._eq(stT.SEND) | st._eq(stT.SEND_wait))
        
        self.oled.spi ** self.spiCntrl.dataOut
    
    def columnHandler(self, st, column):
        stT = st._dtype
        Switch(st)\
        .Case(stT.COLUMN_INCR,
            If(column._eq(self.COLUMNS - 1),
                column ** 0 
            ).Else(
                column ** (column + 1)
            )
        ).Case(stT.COLUMN_CLR,
            column ** 0
        )
        
    def rowHandler(self, st, row):
        stT = st._dtype
        Switch(st)\
        .Case(stT.ROW_INCR,
            If(row._eq(self.ROWS - 1),
                row ** 0
            ).Else(
                row ** (row + 1)
            )
        ).Case(stT.ROW_CLR,
            row ** 0
        )
        
    def charRegHandler(self, st, acc, charReg):
        If(st._eq(st._dtype.STORE_CHAR),
            charReg ** acc
        )
        
    def accHandler(self, st, charBmRow, memData, acc):
        stT = st._dtype
    
        Switch(st)\
        .Case(stT.LOAD_DATA_collectAndIncr,
            acc ** memData
        ).Case(stT.LOAD_BM_ROW_collect,
            acc ** charBmRow 
        ).Case(stT.LOAD_EXTERN,
            acc ** self.dataIn.data
        )
    
    def irHandler(self, st, memData, ir):
        If(st._eq(st._dtype.load),
           ir ** memData
        )
    
    def ipHandler(self, st, ip):
        stT = st._dtype
        If(In(st, [stT.incr_IP, stT.LOAD_DATA_collectAndIncr]),
           ip ** (ip + 1)
        )
    
    def memHandler(self, st, ip):
        mem = self._sig("mem", Array(vecT(8), len(self.PROGRAM)), defVal=self.PROGRAM)
        memData = self._sig("memData", vecT(8))
        stT = st._dtype 
        
        If(self.clk._onRisingEdge(),
            If(In(st, [stT.LOAD_DATA, stT.LOAD_DATA_collectAndIncr]),
                memData ** mem[ip + 1]
            ).Else(
                memData ** mem[ip]
            )
        )
        return memData
    
    def bmMapHandler(self, st):
        charToBitmap = addCharToBitmap(self)
        charBmRow = self._sig("charBmRow", vecT(8))
        charBmRowAddr = self._reg("charBmRowAddr", vecT(8), defVal=0)
        
        If(self.clk._onRisingEdge(),
           charBmRow ** charToBitmap[charBmRowAddr]
        )
        If(st._eq(st._dtype.LOAD_BM_ROW_collect),
            charBmRowAddr ** (charBmRowAddr + 1) 
        )
        
        return charBmRow
