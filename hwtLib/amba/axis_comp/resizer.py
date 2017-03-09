from hwt.code import If, log2ceil, Concat, Switch
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param, evalParam
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.streamNode import streamAck



class AxiSResizer(AxiSCompBase):
    """
    Change data with of interface
    @attention: in upscale mode id and other signals which are not dependent on data width 
                are propagated only from last word
    @attention: in downscale mode strb does not affect if word should be send this means that
                there can be words with strb=0 if strb of input is ton fully set
    """
    def _config(self):
        AxiSCompBase._config(self)
        self.OUT_DATA_WIDTH = Param(64)
        
    def _declr(self):
        addClkRstn(self)
        
        with self._paramsShared():
            self.dataIn = self.intfCls()
            
        with self._paramsShared(exclude=[self.DATA_WIDTH]):
            self.dataOut = self.intfCls()
            self.dataOut._replaceParam("DATA_WIDTH", self.OUT_DATA_WIDTH)
            
    def _impl(self):
        IN_DW = evalParam(self.DATA_WIDTH).val
        OUT_DW = evalParam(self.OUT_DATA_WIDTH).val
        dIn = self.getDataWidthDependent(self.dataIn)
        dOut = self.getDataWidthDependent(self.dataOut)
        
        if IN_DW < OUT_DW:  # UPSCALE
            if OUT_DW % IN_DW != 0:
                raise NotImplementedError()
            ITEMS = OUT_DW // IN_DW 
            itemCntr = self._reg("itemCntr", vecT(log2ceil(ITEMS + 1)), defVal=0)
            hs = streamAck([self.dataIn], [self.dataOut])
            isLastItem = (itemCntr._eq(ITEMS - 1) | self.dataIn.last)
            
            vld = self.getVld(self.dataIn)

            outputs = {outp : [] for outp in dOut}
            for wordIndx in range(ITEMS):
                for inp, outp in zip(dIn, dOut):
                    # generate register if is not last item
                    s = self._sig("item_%d_%s" % (wordIndx, inp._name), inp._dtype)
                    
                    if wordIndx <= ITEMS - 1:
                        r = self._reg("reg_" + inp._name + "_%d" % wordIndx, inp._dtype, defVal=0)

                        If(hs & isLastItem,
                           r ** 0
                        ).Elif(vld & itemCntr._eq(wordIndx),
                           r ** inp
                        )
                        
                        If(itemCntr._eq(wordIndx),
                           s ** inp
                        ).Else(
                           s ** r
                        )
                    else:  # last item does not need register
                        If(itemCntr._eq(wordIndx),
                           s ** inp
                        ).Else(
                           s ** 0
                        )
                    
                    outputs[outp].append(s)

            # dataIn/dataOut hs
            self.getRd(self.dataIn) ** self.getRd(self.dataOut)
            self.getVld(self.dataOut) ** (self.getVld(self.dataIn) & (isLastItem))    

            # connect others signals directly
            for inp, outp in zip(self.getData(self.dataIn), self.getData(self.dataOut)):
                if inp not in dIn:
                    outp ** inp
            
            # connect data signals to utput
            for outp, outItems in outputs.items():
                outp ** Concat(*reversed(outItems))
            
            # itemCntr next logic
            If(hs,
                If(isLastItem,
                    itemCntr ** 0
                ).Else(
                    itemCntr ** (itemCntr + 1)
                )
            )
        
        elif IN_DW > OUT_DW:  # DOWNSCALE
            if IN_DW % OUT_DW != 0:
                raise NotImplementedError()
            
            ITEMS = IN_DW // OUT_DW  
            itemCntr = self._reg("itemCntr", vecT(log2ceil(ITEMS + 1)), defVal=0)
            hs = streamAck([self.dataIn], [self.dataOut])
            isLastItem = itemCntr._eq(ITEMS - 1)
            
            # connected item selected by itemCntr to output
            for inp, outp in zip(dIn, dOut):
                w = outp._dtype.bit_length()
                Switch(itemCntr)\
                .addCases([
                    (wordIndx, outp ** inp[((wordIndx+1)*w):(w*wordIndx)]) 
                      for wordIndx in range(ITEMS)
                    ])
            
            # connect others signals directly
            for inp, outp in zip(self.getData(self.dataIn), self.getData(self.dataOut)):
                if inp not in dIn and inp is not self.dataIn.last:
                    outp ** inp    
            
            self.dataOut.last ** (self.dataIn.last & isLastItem)    
            self.getRd(self.dataIn) ** (self.getRd(self.dataOut) & isLastItem)
            self.getVld(self.dataOut) ** self.getVld(self.dataIn)
             
        else:  # same
            self.dataOut ** self.dataIn
        
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.amba.axis import AxiStream_withId
    
    u = AxiSResizer(AxiStream_withId)
    u.DATA_WIDTH.set(128)
    u.OUT_DATA_WIDTH.set(32)
    print(toRtl(u))
