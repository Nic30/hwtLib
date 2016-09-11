from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.hdlObjects.types.array import Array
from hdl_toolkit.interfaces.std import FifoWriter, FifoReader
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param


class Fifo(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.DEPTH = Param(200)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.dataIn = FifoWriter()
                self.dataOut = FifoReader()
    
    def _impl(self):
        index_t = vecT(log2ceil(self.DEPTH), False)
        
        self.mem = self._sig("memory", Array(vecT(self.DATA_WIDTH), self.DEPTH))
        mem = self.mem
        head = self._reg("head", index_t, 0)
        tail = self._reg("tail", index_t, 0)
        looped = self._reg("looped", defVal=False)
        
        DEPTH = self.DEPTH
        
        dout = self.dataOut
        din = self.dataIn

        MAX_DEPTH = DEPTH - 1
        # [TODO] forgot head, tail clock enable 
                
        rd_en = dout.en & (looped | (head != tail))
        If(rd_en,
            # Update data output
            dout.data ** mem[tail] 
        ).Else(
            dout.data ** None
        ) 
        # Update Tail pointer as needed
        If(rd_en,
            If(tail._eq(MAX_DEPTH),
               tail ** 0 
            ).Else(
               tail ** (tail + 1)
            )
        )
        
        wr_en = din.en & (~looped | (head != tail))
        If(self.clk._onRisingEdge() & wr_en,
            # Write Data to Memory
            mem[head] ** din.data
        )                 
        # Increment Head pointer as needed
        If(wr_en,
            If(head._eq(MAX_DEPTH),
                head ** 0
            ).Else(
                head ** (head + 1) 
            )
        )
        # looped logic
        If(din.en & head._eq(MAX_DEPTH),
            looped ** True
        ).Elif(dout.en & tail._eq(MAX_DEPTH),
            looped ** False
        )
                
        # Update Empty and Full flags
        If(head._eq(tail),
            If(looped,
                din.wait ** 1,
                dout.wait ** 0 
            ).Else(
                dout.wait ** 1,
                din.wait ** 0
            )
        ).Else(
            din.wait ** 0,
            dout.wait ** 0 
        )

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(Fifo))

