from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If




class FifoLogic(Unit):
    """
    Simplified example of fifo logic used for debugging purposes
    """
    def _config(self):
        self.DEPTH = Param(200)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.dIn_wait = Signal()
            self.dIn_en = Signal()
            
            self.dOut_wait = Signal()
            self.dOut_en = Signal()
            
            self.looped = Signal()
    
    def _impl(self):
        index_t = vecT(log2ceil(self.DEPTH), False)
        
        head = self._reg("head", index_t, 0)
        tail = self._reg("tail", index_t, 0)
        looped = self._reg("reg_looped",  defVal=False)
        
        DEPTH = self.DEPTH
        
        MAX_DEPTH = DEPTH -1
        
        dOut_en = self.dOut_en
        dIn_en = self.dIn_en
                
        rd_en = dOut_en & (looped | (head != tail))
        # Update Tail pointer as needed
        If(rd_en,
            If(tail._eq(MAX_DEPTH),
               c(0, tail) 
               ,
               c(tail + 1, tail)
            )
            ,
            c(tail, tail)
        )
        
        wr_en = dIn_en & (~looped | (head != tail))
        # Increment Head pointer as needed
        If(wr_en,
            If(head._eq(MAX_DEPTH),
                c(0, head)
                ,
                c(head + 1, head) 
            )
           ,
           c(head, head)
        )
        If(rd_en & head._eq(MAX_DEPTH),
           c(True, looped)
           ,
           If(wr_en & head._eq(MAX_DEPTH),
               c(False, looped)
               ,
               c(looped, looped)
           )
        )
        c(looped, self.looped)        
                

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
    from hdl_toolkit.simulator.shortcuts import simUnitVcd, oscilate, pullUpAfter
    
    u = FifoLogic()
    #print(
    toRtl(u)
    #)
   
    u.DEPTH.set(4)
    ns = HdlSimulator.ns
    
    def dinEn(s):
        s.write(1, u.dIn_en)
        while True:
            yield s.wait(7*ns)
            #s.write(~s.read(u.dIn_en), u.dIn_en)
        
    def dataStimul(s):
        w = s.write
        w(0, u.dIn_en)
        
        w(0, u.dOut_en)
        yield s.wait(10)

    simUnitVcd(u, [oscilate(u.clk),
                   pullUpAfter(u.rst_n, 9*ns),
                   dataStimul,
                   dinEn],
                "tmp/fifoLogic.vcd", 
                time=120 * HdlSimulator.ns)
    print("done")

