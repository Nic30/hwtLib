from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hdl_toolkit.synthetisator.interfaceLevel.interface import Interface
from hdl_toolkit.interfaces.spi import SPI
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.hdlObjects.types.enum import Enum

from hwtLib.spi.controller import SPICntrlW
from hwtLib.logic.delayMs import DelayMs
from hdl_toolkit.synthetisator.codeOps import c, Switch, If, In, FsmBuilder
from hdl_toolkit.hdlObjects.typeShortcuts import vecT, vec

class OledIntf(Interface):
    def _config(self):
        DelayMs._config(self)
    
    def _declr(self):
        self.spi = SPI()
        self.dc = Signal()  # Data/Command Pin
        self.res = Signal()  # PmodOLED RES
        self.vbat = Signal()  # VBAT enable
        self.vdd = Signal()  # VDD enable
 
class OledCntrl(Unit):
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.oled = OledIntf()
            self.dataIndone = Signal()  # OledCntrl Finish Flag
        
        
        # [TODO] clk prescaler always should be 33mhz
        self.cntrl = SPICntrlW()
        
        with self._paramsShared():
            self.delay = DelayMs()
        
    def temp_spi_enDriver(self,st, temp_spi_en):
        stT = st._dtype
        
        Switch(st)\
        .Case(st.transition1,
           c(1, temp_spi_en)
        ).Case(stT.transition5,
            c(0, temp_spi_en)
        ).Default(
            temp_spi_en._same()     
        )
        
    def temp_delay_enDriver(self, st, temp_delay_en):
        stT = st._dtype
        
        Switch(st)\
        .Case(st.Transition3,
           c(1, temp_delay_en)
        ).Case(stT.Transition5,
            c(0, temp_delay_en)
        ).Default(
            temp_delay_en._same()     
        )
       
    def oledTransitions(self, st, stCase, after_state, temp_spi_fin, temp_delay_fin):
        stT = st._dtype
        
        # SPI transitions
        # 1. Set SPI_EN to 1
        # 2. Waits for SpiCtrl to finish
        # 3. Goes to clear state (Transition5)
        return stCase.Case(stT.transition1,
            c(stT.transition2,st),
            after_state._same()
        ).Case(stT.transition2,
            If(temp_spi_fin,
                c(stT.transition5, st)
            ).Else(
                st._same()
            ),
            after_state._same()
        ).Case(stT.transition3,
            # Delay Transitions
            # 1. Set DELAY_EN to 1
            # 2. Waits for Delay to finish
            # 3. Goes to Clear state (Transition5)    
            c(stT.transition4, st),
                after_state._same()
        ).Case(stT.transition4,
            If(temp_delay_fin,
               c(stT.transition5, st)
            ).Else(
                st._same()
            ),
            after_state._same()
        ).Case(stT.transition5,
            # Clear transition
            # 1. Sets both DELAY_EN and SPI_EN to 0
            # 2. Go to after state
            c(after_state, st),
            after_state._same()
        )

    def charSending(self, st, after_state, temp_char, temp_addr, after_char_state):
        #charRowIndex = self._reg("charRowIndex", vecT(3), 0)
        #Switch()
        stT = st._dtype
        sendCharStates = [getattr(stT, "sendChar%d" % i) for i in range(8)]
        # temp_addr driver
        Switch(st).addCases( 
            [
             (state, c(temp_char._concat(vec(i, 3)), temp_addr))  
                   for i, state in enumerate(sendCharStates)
            ]
        ).Default(
            temp_addr._same()
        )
        
        stCases = []
        # sendchar state shift
        nextSt = iter(sendCharStates)
        for s in sendCharStates:
            (s, )
        
    def _impl(self):
        propagateClkRstn(self)
        temp_addr = self._reg("temp_addr",vecT(10))
        temp_char = self._reg("temp_char", vecT(8))
        
        oled = self.oled

        c(0, oled.dc)
        #c(~self.rst_n)
    
    def mainFsm(self):
        initialized = self._reg("initialized",  defVal=0)
        initDataAddr = self._reg("initDataAddr", vecT(log2ceil(len(initSequence))))
        stT = Enum("stT", [
                           "idle",
                           "transition1",
                           "transition2",
                           "transition3",
                           "transition4",
                           "transition5",
                           "vddOn",
                           "wait1",
                           "resetOn",
                           "wait2",
                           "resetOff",
                           "vbatOn",
                           "wait3",
                          
                           "dispOn",
                           "fullDisp",
                           "done",
                           "VCOMH2",
                           
                           ])
        afterSt = Enum("afterSt", stT)
       
        If(initialized,
           initialized._same()
        ).Else(
           c(1, initialized)
        )
        
        #doTransmit = [stT.dispOff, stT.setClockDiv1, stT.setClockDiv2, stT.multiPlex1, stT.multiPlex2, 
        #    stT.cargePump1, stT.chargePump2,  stT.preCharge1, stT.preCharge2, stT.VCOMH2, 
        #    stT.dispContrast1, stT.dispContrast1, stT.invertDisp1, stT.invertDisp2, stT.comConfig1, stT.comConfig1]
        
        #fsmB = FsmBuilder(stT)
        #st = fsmB.stateReg
        
        #If(In(st, doTransmit))
        
        
        #fsmB.Trans(stT.idle,
        #    (initialized, stT.waitRequest),
        #    stT.vddOn
        #).Trans(stT.vddOn,
        #    stT.wait1   
        #).Trans(stT.wait1,
        #    stT.transition3
        #).Trans(stT.sendInitData
        #    
        #)

        st = self._reg("st", stT, stT.idle)
        afterState = self._reg("afterState", stT, stT.idle)
        


    def genInitFsm(self):


if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = OledInit()
    print(toRtl(u))