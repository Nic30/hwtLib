from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil
from hdl_toolkit.interfaces.std import FifoWriter, FifoReader
from hdl_toolkit.hdlObjects.types.array import Array
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If
from hdl_toolkit.hdlObjects.types.defs import INT


class Fifo(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.DEPTH = Param(200)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.dIn = FifoWriter()
            self.dOut = FifoReader()
            self._shareAllParams()
    
    def _impl(self):
        index_t = vecT(log2ceil(self.DEPTH), False)
        
        self.mem = self._sig("memory", Array(vecT(self.DATA_WIDTH), self.DEPTH))
        mem = self.mem
        head = self._reg("head", index_t, 0)
        tail = self._reg("tail", index_t, 0)
        looped = self._reg("looped",  defVal=False)
        DEPTH = self.DEPTH
        
        dOut = self.dOut
        dIn = self.dIn

        
        rd_en = dOut.en & looped | (head != tail)
        If(self.clk._onRisingEdge() & rd_en,
           # Update data output
            c(mem[tail], dOut.data) 
        ) 
        # Update Tail pointer as needed
        If(rd_en & tail._convert(INT)._eq(self.DEPTH - 1),
            c(0, tail) 
            ,
            c(tail + 1, tail)
        )
        
        wr_en = dIn.en & ~looped | (head != tail)
        If(self.clk._onRisingEdge() & wr_en,
            # Write Data to Memory
            c(dIn.data, mem[head])
        )                 
        # Increment Head pointer as needed
        If(wr_en & head._convert(INT)._eq(DEPTH - 1),
            c(0, head)
            ,
            c(head + 1, head) 
        )
        If(rd_en & head._convert(INT)._eq(DEPTH - 1),
           c(True, looped)
           ,
           If (wr_en & head._convert(INT)._eq(DEPTH - 1),
               c(False, looped)
               ,
               c(looped, looped)
           )
        )
        c(looped)        
                
        # Update Empty and Full flags
        If(head._eq(tail),
            If(looped,
                c(1, dIn.wait)
                ,
                c(1, dOut.wait)
            )
            ,
            c(0, dIn.wait) +
            c(0, dOut.wait)
        )

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(Fifo))

