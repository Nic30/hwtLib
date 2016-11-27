#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hBit
from hdl_toolkit.hdlObjects.types.array import Array
from hdl_toolkit.interfaces.std import FifoWriter, FifoReader, VectSignal
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil, isPow2
from hdl_toolkit.serializer.constants import SERI_MODE
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
# https://eewiki.net/pages/viewpage.action?pageId=20939499

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
                self.size = VectSignal(log2ceil(self.DEPTH + 1), signed=False) 
    
    def _impl(self):
        DEPTH = self.DEPTH
        assert evalParam(DEPTH).val > 0
        
        index_t = vecT(log2ceil(DEPTH), False)
        
        mem = self.mem = self._sig("memory", Array(vecT(self.DATA_WIDTH), self.DEPTH))
        wr_ptr = self._reg("wr_ptr", index_t, 0)
        rd_ptr = self._reg("rd_ptr", index_t, 0)
        LATENCY = evalParam(self.LATENCY).val
        EXPORT_SIZE = evalParam(self.EXPORT_SIZE).val
        MAX_DEPTH = DEPTH - 1
        
        dout = self.dataOut
        din = self.dataIn
        
        fifo_write = self._sig("fifo_write")
        fifo_read = self._sig("fifo_read")

        # Update Tail pointer as needed
        If(fifo_read,
            If(rd_ptr._eq(MAX_DEPTH),
               rd_ptr ** 0 
            ).Else(
               rd_ptr ** (rd_ptr + 1)
            )
        )
        
        # Increment Head pointer as needed
        If(fifo_write,
            If(wr_ptr._eq(MAX_DEPTH),
                wr_ptr ** 0
            ).Else(
                wr_ptr ** (wr_ptr + 1) 
            )
        )
        
        If(self.clk._onRisingEdge(),
            If(fifo_write,
                # Write Data to Memory
                mem[wr_ptr] ** din.data
            )     
        )
        
        if LATENCY == 1: 
            # assert isPow2(evalParam(DEPTH).val), DEPTH
            
            looped = self._reg("looped", defVal=False)
            
            fifo_read ** (dout.en & (looped | (wr_ptr != rd_ptr)))
            If(fifo_read,
                # Update data output
                dout.data ** mem[rd_ptr] 
            ).Else(
                dout.data ** None
            ) 
            
            fifo_write ** (din.en & (~looped | (wr_ptr != rd_ptr)))
            

            # looped logic
            If(din.en & wr_ptr._eq(MAX_DEPTH),
                looped ** True
            ).Elif(dout.en & rd_ptr._eq(MAX_DEPTH),
                looped ** False
            )
                    
            # Update Empty and Full flags
            If(wr_ptr._eq(rd_ptr),
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
                size = self._reg("size_reg", self.size._dtype, 0)
                If(fifo_read,
                    If(~fifo_write,
                       size ** (size - 1)
                    )
                ).Else(
                    If(fifo_write,
                       size ** (size + 1)
                    )
                )
                self.size ** size
                
            
        elif LATENCY == 2:
            assert isPow2(evalParam(DEPTH).val), DEPTH
            if EXPORT_SIZE: 
                raise NotImplementedError() 
            
            empty_flag = self._sig("empty_flag")
            full_flag = self._sig("full_flag")

            If(self.clk._onRisingEdge(),
                If(fifo_read,
                    # Update data output
                    dout.data ** mem[rd_ptr] 
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
            
            full_flag ** rd_ptr._eq(wr_ptr + 1)
            empty_flag ** wr_ptr._eq(rd_ptr)
            fifo_write ** (din.en & (~full_flag | (full_flag & dout.en)))
            din.wait ** full_flag
            
            
        else:
            raise NotImplementedError("%r not implemented for latency %d" % (self, LATENCY))

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = Fifo()
    u.LATENCY.set(2)
    # u.EXPORT_SIZE.set(True)
    u.DEPTH.set(128)
    print(toRtl(u))

