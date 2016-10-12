from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hwtLib.mem.fifo import Fifo
from hdl_toolkit.synthesizer.param import Param
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil, propagateClkRstn
from hwtLib.interfaces.amba import AxiStream
from hdl_toolkit.interfaces.std import Handshaked
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.axi.axis_fifo import AxiSFifo
from hwtLib.axi.axis_builder import AxiSBuilder
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthesizer.codeOps import If, connect, Concat, Switch
from hdl_toolkit.bitmask import mask

def strbToRem(strbBits):
    """
    @return: tuples (mask, numberofBits) 
    
    """
    for rem in range(strbBits):
        if (rem == 0):
            strb = mask(strbBits)
        else:
            strb = mask(rem)
        yield strb, rem

class AxiS_measuringFifo(Unit):
    """
    Fifo which are counting sizes of frames and sends it over
    dedicated handshaked interface
    """
    def _config(self):
        Fifo._config(self)
        self.SIZES_BUFF_DEPTH = Param(16) 
        self.MAX_LEN = Param(4096 // 8 - 1)
    
    def getAliginBitsCnt(self):
        return log2ceil(self.DATA_WIDTH // 8).val
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.dataIn = AxiStream()
                self.dataOut = AxiStream()
            
            self.sizes = Handshaked()
            self.sizes.DATA_WIDTH.set(log2ceil(self.MAX_LEN) + self.getAliginBitsCnt())
        
        db = self.dataBuff = AxiSFifo(AxiStream)
        # to place fifo in bram
        db.LATENCY.set(2)
        db.DATA_WIDTH.set(self.DATA_WIDTH)
        db.DEPTH.set((self.MAX_LEN + 1) * 2)
        
        sb = self.sizesBuff = HandshakedFifo(Handshaked)
        sb.DEPTH.set(self.SIZES_BUFF_DEPTH)
        sb.DATA_WIDTH.set(self.sizes.DATA_WIDTH.get()) 
        
    def _impl(self):
        propagateClkRstn(self)
        dIn = AxiSBuilder(self, self.dataIn).reg().end
        STRB_BITS = dIn.strb._dtype.bit_length()
        
        sb = self.sizesBuff
        db = self.dataBuff
        
        self.sizes ** sb.dataOut
        self.dataOut ** db.dataOut
        
        wordCntr = self._reg("wordCntr",
                             vecT(log2ceil(self.MAX_LEN)),
                             defVal=0)
        dIn.ready ** (sb.dataIn.rd & db.dataIn.ready)
        If(dIn.valid & sb.dataIn.rd & db.dataIn.ready,
            If(dIn.last,
                wordCntr ** 0
            ).Else(
                wordCntr ** (wordCntr + 1)
            )
        )
        rem = self._sig("rem", vecT(log2ceil(STRB_BITS)))
        Switch(dIn.strb).addCases(
           [(strb, rem ** r) for strb, r in strbToRem(STRB_BITS)]
        ).Default(
            rem ** 0
        )    
        
        
        length = self._sig("length", wordCntr._dtype)
        
        
        If(dIn.strb != mask(dIn.strb._dtype.bit_length()),
            length ** wordCntr
        ).Else(
            length ** (wordCntr + 1)
        )
        
        sb.dataIn.data ** Concat(length, rem)
        
        
        sb.dataIn.vld ** (dIn.valid & dIn.last & db.dataIn.ready)
        db.dataIn.valid ** (dIn.valid & sb.dataIn.rd)
        
        connect(dIn, db.dataIn, exclude=[dIn.valid, dIn.ready])
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = AxiS_measuringFifo()
    print(toRtl(u))
    
