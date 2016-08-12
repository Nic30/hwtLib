from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal, VldSynced
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.synthesizer.codeOps import If, c
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param


class FlipRegister(Unit):
    """
    Switchable register, there are two registers and two sets of ports,
    Each set of ports is every time connected to opposite reg.
    By select you can choose between regs.
    
    This component is meant to be form of synchronization.
    Example first reg is connected to first set of ports, writer performs actualizations on first reg
    and reader reads data from second ram by second set of ports.
    
    Then select is set and access is flipped. Reader now has access to reg 0 and writer to reg 1.
    """
    
    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.DEFAULT_VAL = Param(0)
        
    def _declr(self):
        d_t = vecT(self.DATA_WIDTH)
        with self._asExtern(), self._paramsShared():
            addClkRstn(self)
            self.firstIn = VldSynced()
            self.firstOut = Signal(dtype=d_t)
            
            self.secondIn = VldSynced()
            self.secondOut = Signal(dtype=d_t)
            
            self.select_sig = Signal()
    
    def connectWriteIntf(self, regA, regB):
        return (
            If(self.firstIn.vld,
                c(self.firstIn.data, regA)
            ).Else(
                c(regA, regA)
            )+
            If(self.secondIn.vld,
               c(self.secondIn.data, regB)
            ).Else(
               c(regB, regB)
            )
        )
            
    def connectReadIntf(self, regA, regB):
        return (c(regA, self.firstOut) +
                c(regB, self.secondOut)
                )
     
    def _impl(self):
        first = self._reg("first_reg", vecT(self.DATA_WIDTH), defVal=self.DEFAULT_VAL)
        second = self._reg("second_reg", vecT(self.DATA_WIDTH), defVal=self.DEFAULT_VAL)
        
        If(self.select_sig,
           self.connectWriteIntf(second, first) +
           self.connectReadIntf(second, first)
        ).Else(
           self.connectReadIntf(first, second) +
           self.connectWriteIntf(first, second)
        )
        
if __name__ == "__main__": # alias python main function
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(FlipRegister))
