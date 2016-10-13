#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.hdlObjects.types.array import Array
from hdl_toolkit.interfaces.std import FifoWriter, FifoReader, VectSignal
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil, isPow2
from hdl_toolkit.serializer.constants import SERI_MODE
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam


class Fifo(Unit):
    """
    If LATENCY == 1 
       lutram implementation
    if LATENCY == 2
       bram implementation
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ
    
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.LATENCY = Param(1)
        self.DEPTH = Param(200)
        self.EXPORT_SIZE = Param(False)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.dataIn = FifoWriter()
                self.dataOut = FifoReader()
            
            if evalParam(self.EXPORT_SIZE).val:
                self.size = VectSignal(log2ceil(self.DEPTH), signed=False) 
    
    def _impl(self):
        index_t = vecT(log2ceil(self.DEPTH), False)
        
        mem = self.mem = self._sig("memory", Array(vecT(self.DATA_WIDTH), self.DEPTH))
        head = self._reg("head", index_t, 0)
        tail = self._reg("tail", index_t, 0)
        LATENCY = evalParam(self.LATENCY).val
        DEPTH = self.DEPTH
        EXPORT_SIZE = evalParam(self.EXPORT_SIZE).val
        MAX_DEPTH = DEPTH - 1
        
        dout = self.dataOut
        din = self.dataIn
        
        fifo_write = self._sig("fifo_write")
        fifo_read = self._sig("fifo_read")

        # Update Tail pointer as needed
        If(fifo_read,
            If(tail._eq(MAX_DEPTH),
               tail ** 0 
            ).Else(
               tail ** (tail + 1)
            )
        )
        
        # Increment Head pointer as needed
        If(fifo_write,
            If(head._eq(MAX_DEPTH),
                head ** 0
            ).Else(
                head ** (head + 1) 
            )
        )
        
        If(self.clk._onRisingEdge() & fifo_write,
            # Write Data to Memory
            mem[head] ** din.data
        )     
        
        if LATENCY == 1:
            looped = self._reg("looped", defVal=False)
            
            fifo_read ** (dout.en & (looped | (head != tail)))
            If(fifo_read,
                # Update data output
                dout.data ** mem[tail] 
            ).Else(
                dout.data ** None
            ) 
            
            fifo_write ** (din.en & (~looped | (head != tail)))
            

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
            if EXPORT_SIZE:
                If(looped,
                    self.size ** DEPTH
                ).Elif(head < tail,
                    self.size ** (DEPTH - tail + head)
                ).Else(
                    self.size ** (head - tail)     
                )
            
        elif LATENCY == 2:
            assert isPow2(evalParam(DEPTH).val), DEPTH
            if EXPORT_SIZE: raise NotImplementedError() 
            empty_flag = self._sig("empty_flag")
            full_flag = self._sig("full_flag")

            If(self.clk._onRisingEdge(),
                If(fifo_read,
                    # Update data output
                    dout.data ** mem[tail] 
                ).Else(
                    dout.data ** None
                )
            )
            
            isEmpty = self._reg("isEmpty", defVal=1)
            If(isEmpty & ~empty_flag,
                isEmpty ** 0
            ).Elif(~isEmpty & empty_flag & dout.en,
                isEmpty ** 1
            )
            
            If(isEmpty & ~empty_flag,
                fifo_read ** 1,
            ).Elif(~isEmpty & ~empty_flag & dout.en,
                fifo_read ** 1,
            ).Else(
                fifo_read ** 0
            )
            
            dout.wait ** isEmpty
            
            full_flag ** tail._eq(head + 1)
            empty_flag ** head._eq(tail)
            fifo_write ** (din.en & (~full_flag | (full_flag & dout.en)))
            din.wait ** full_flag
            
            
        else:
            raise NotImplementedError("%r not implemented for latency %d" % (self, LATENCY))

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = Fifo()
    u.EXPORT_SIZE.set(True)
    u.DEPTH.set(128)
    print(toRtl(u))

