from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
from hdl_toolkit.interfaces.std import Handshaked, Signal
from hdl_toolkit.synthesizer.codeOps import FsmBuilder, Switch, If, connect
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.utils import addClkRstn


IDLE = 0
START = 0b0100
BIT0 = 0b1000 
BIT1 = 0b1001 
BIT2 = 0b1010 
BIT3 = 0b1011 
BIT4 = 0b1100 
BIT5 = 0b1101 
BIT6 = 0b1110 
BIT7 = 0b1111 
STOP1 = 0b0001 
STOP2 = 0b0010 

class UartTx(Unit):
    def _config(self):
        self.FREQ = Param(int(100e6))
        self.BAUD = Param(115200)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.dataIn = Handshaked()
            self.dataIn.DATA_WIDTH.set(8)
            self.txd = Signal()
    
    def _impl(self):
        baudCntrWidth = 16
        baud = evalParam(self.BAUD).val
        freq = evalParam(self.FREQ).val
        
        baudCntrInc = ((baud << (baudCntrWidth - 4)) + (freq >> 5)) // (freq >> 4)
        
        # reset is not needen because uart is "unreliable" and it does not matter
        # if we send wrong data on the begining 
        baudCntr = self._reg("baudCntr", vecT(baudCntrWidth + 1, signed=False))
        tick = baudCntr[baudCntrWidth]
        
        
        st = FsmBuilder(self, vecT(4))\
        .Trans(IDLE,
               (self.dataIn.vld, START)
        ).Trans(START,
               (tick, BIT0)
        ).Trans(BIT0,
               (tick, BIT1)
        ).Trans(BIT1,
               (tick, BIT2)
        ).Trans(BIT2,
               (tick, BIT3)
        ).Trans(BIT3,
               (tick, BIT4)
        ).Trans(BIT4,
               (tick, BIT5)
        ).Trans(BIT5,
               (tick, BIT6)
        ).Trans(BIT6,
               (tick, BIT7)
        ).Trans(BIT7,
               (tick, STOP1)
        ).Trans(STOP1,
               (tick, STOP2)
        ).Trans(STOP2,
               (tick, IDLE)
        ).stateReg
        bussy = st != 0
        dinReg = self._reg("dataIn_reg", vecT(8))
        
        If(bussy,
            dinReg._same(),
            connect(baudCntr[baudCntrWidth:0] + baudCntrInc, baudCntr, fit=True)
        ).Else(
            dinReg ** self.dataIn.data,
            baudCntr._same()
        )
        self.dataIn.rd ** ~bussy
        
        muxBit = self._sig("muxBit")
        Switch(st[3:]).addCases(
            [(i , muxBit ** dinReg[i]) 
             for i in range(8)])
    
        
        txReg = self._reg("txReg")
        txReg ** ((st < 4) | (st[3] & muxBit))
        self.txd ** txReg
 
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = UartTx()
    print(toRtl(u)) 
        
