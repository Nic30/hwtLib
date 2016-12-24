from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.utils import addClkRstn
from hwt.code import If, Concat, log2ceil
from hwt.synthesizer.param import Param, evalParam
from hwtLib.handshaked.compBase import HandshakedCompBase


class HandshakedResizer(HandshakedCompBase):
    """
    Resize width handshaked iterface
    
    [TODO] implementation for |IN| > |OUT|
    """
    def _shareParamsWithMultiplier(self, other, multiplier):
        def updater(self, onParentName, p):
            getattr(self, onParentName).set(p * multiplier)
            
        other._updateParamsFrom(self, updater)
    
    def _config(self):
        super()._config()
        self.OUT_MULTIPLIER = Param(2)
            
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = self.intfCls()
        
        self.dataOut = self.intfCls()
        self._shareParamsWithMultiplier(self.dataOut, self.OUT_MULTIPLIER)
    
    def dataPassLogic(self, inputRegs_cntr):
        MULTIPLIER = evalParam(self.OUT_MULTIPLIER).val
        
        # valid when all registers are loaded and input with last datapart is valid 
        self.getVld(self.dataOut) ** (inputRegs_cntr._eq(MULTIPLIER) & self.getVld(self.dataIn))
        
        self.getRd(self.dataIn) ** ((inputRegs_cntr != MULTIPLIER) | self.getRd(self.dataOut))
        If(inputRegs_cntr._eq(MULTIPLIER - 1),
            If(self.getVld(self.dataIn) & self.getRd(self.dataOut),
               inputRegs_cntr ** 0
            )
        ).Else(
            If(self.getVld(self.dataIn),
               inputRegs_cntr ** (inputRegs_cntr + 1)
            )
        )

    def _impl(self):
        MULTIPLIER = evalParam(self.OUT_MULTIPLIER).val
        assert MULTIPLIER >= 1
        if MULTIPLIER == 1:
            self.dataOut ** self.dataIn
            return 
        
        inputRegs_cntr = self._reg("inputRegs_cntr",
                                   vecT(log2ceil(MULTIPLIER + 1), False),
                                   defVal=0)
        
        for din, dout in zip(self.getData(self.dataIn), self.getData(self.dataOut)):
            inputRegs = [self._reg("inReg%d_%s" % (i, din._name), din._dtype)
                            for i in range(MULTIPLIER - 1) ]
        
            for i, r in enumerate(inputRegs):
                If(inputRegs_cntr._eq(i) & self.getVld(self.dataIn),
                   r ** din
                )
            dout ** Concat(din, *inputRegs)
        self.dataPassLogic(inputRegs_cntr)    

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwt.interfaces.std import Handshaked
    u = HandshakedResizer(Handshaked)
    print(toRtl(u))
