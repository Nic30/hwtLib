from hwtLib.mem.fifo import Fifo
from hdl_toolkit.interfaces.std import Clk, Rst_n, FifoWriter, FifoReader
from hwtLib.logic.cntrGray import GrayCntr
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.hdlObjects.types.array import Array
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c
from hdl_toolkit.interfaces.utils import log2ceil

class AsyncFifo(Fifo):
    def _declr(self):
        with self._asExtern():
            self.dataIn_clk = Clk() 
            self.dataOut_clk = Clk()
            self.rst_n = Rst_n()
            
            with self._paramsShared():
                self.dataIn = FifoWriter()
                self.dataOut = FifoReader()
        
        
        self.pWr = GrayCntr()
        self.pRd = GrayCntr()
        self.addrW = log2ceil(self.DEPTH)

        for cntr in [self.pWr, self.pRd]:
            cntr.DATA_WIDTH.set(self.addrW)
    
    def _impl(self):
        mem_t = Array(vecT(self.DATA_WIDTH), self.DEPTH)
        mem = self._sig("mem", mem_t)
        full = self._sig("full")
        empty = self._sig("empty")
        status = self._sig("status")
        
        In = self.dataIn
        InClk = self.dataIn_clk._onRisingEdge()
        Out = self.dataOut
        OutClk = self.dataOut_clk._onRisingEdge()

        c(In.en & ~full,   self.pWr.en)
        c(self.dataIn_clk, self.pWr.clk)
        c(self.rst_n,      self.pWr.rst_n)
        pNextWordToWrite = self.pWr.dataOut
        

        c(Out.en & ~empty,  self.pRd.en)
        c(self.dataOut_clk, self.pRd.clk)
        c(self.rst_n,       self.pRd.rst_n)
        pNextWordToRead = self.pRd.dataOut
        

        # data out logic
        If(OutClk,
            If(Out.en & ~empty,
               c(mem[pNextWordToRead], Out.data) 
            )
        )

        # data in logic
        If(InClk,
            If(In.en & ~full,
               c(In.data, mem[pNextWordToWrite]) 
            )
        )

        equalAddresses = pNextWordToWrite._eq(pNextWordToRead)

        aw = self.addrW
        nw = pNextWordToWrite
        nr = pNextWordToRead
        setStatus = nw[aw - 2]._eq(nr[aw - 1]) & (nw[aw - 1] ^ nr[aw - 2])
        rstStatus = (nw[aw - 2] ^ nr[aw - 1]) & nw[aw - 1]._eq(nr[aw - 2])

        # status ltching
        If(rstStatus | self.rst_n._isOn(),
            c(0, status)  # Going 'Empty'.
            ,
            If(setStatus,
               c(1, status)  # Going 'Full'.
            )
        )

        # data in logic
        presetFull = status and equalAddresses

        # D Flip-Flop w/ Asynchronous Preset.
        If(presetFull,
            c(1, full)
            ,
            If(InClk,
               c(0, full)
            )
        )
        c(full, In.wait)

        # data out logic
        presetEmpty = ~status & equalAddresses
        
        # D Flip-Flop w/ Asynchronous Preset.
        If(presetEmpty,
            c(1, empty)
            ,
            If(OutClk,
               c(0, empty)
            )
        )
        c(empty, Out.wait)
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(AsyncFifo))
