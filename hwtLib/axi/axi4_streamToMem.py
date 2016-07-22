from python_toolkit.arrayQuery import where

from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.interfaces.amba import AxiLite, Axi4, BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT
from hdl_toolkit.synthetisator.codeOps import c, Concat, If, Switch
from hdl_toolkit.interfaces.std import Handshaked
from hwtLib.axi.axiLite_regs import AxiLiteRegs
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.hdlObjects.types.defs import BIT
from hdl_toolkit.hdlObjects.typeShortcuts import vec, vecT
from hdl_toolkit.bitmask import Bitmask



class Axi4streamToMem(Unit):
    """
    Most simple DMA for AXI4 interface.
    
    0x0 control reg.
       rw bit 0 - on/off (1 means on)
       r  bit 1 - idle
    0x4 baseAddr
    
    Length of written data is specified by DATA_LEN.
    Input data is splited on smaller frames to fit MAX_BUTST_LEN.
    
    If there is transaction pending idle flag is 0, if on/off is set to 0 in this state 
    unit continues until all data are send and then stayes off.
    This could be use as synchronization with the software.
    
    1) driver enables this unit, then tests while not idle.
    2) then waits while idle. 
    3) then reads the data and back to 1
    
    or unit is enabled and driver disables it only for the time of reading.
    
    """
    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.ADDR_WIDTH = Param(32)
        self.DATA_LEN = Param(33)  # size of data which should be transfered in worlds
        self.MAX_BUTST_LEN = Param(16) 
        self.REGISTER_MAP = [(0x0, "control"),
                             (0x4, "baseAddr")]
    def _declr(self):
        with self._paramsShared():
            with self._asExtern():
                addClkRstn(self)
                self.cntrl = AxiLite()
                self.axi = Axi4()
                self.dataIn = Handshaked()
            self.regsConventor = AxiLiteRegs(self.REGISTER_MAP)
    
    def axiWAddrHandler(self, st, baseAddr, actualAddr, lenRem):
        """
        AXI write addr logic
        """
        axi = self.axi
        st_t = st._dtype
        
        c(st._eq(st_t.writeAddr), axi.aw.valid)
        c(actualAddr, axi.aw.addr)
        c(0, axi.aw.id)
        c(BURST_INCR, axi.aw.burst) 
        c(CACHE_DEFAULT, axi.aw.cache)
        If(lenRem > self.MAX_BUTST_LEN,
            c(self.MAX_BUTST_LEN, axi.aw.len)
        ).Else(
            c((lenRem - 1)[axi.aw.len._dtype.bit_length():], axi.aw.len)
        )
        c(LOCK_DEFAULT, axi.aw.lock)
        c(PROT_DEFAULT, axi.aw.prot)
        c(BYTES_IN_TRANS(evalParam(self.DATA_WIDTH).val // 8), axi.aw.size)
        c(QOS_DEFAULT, axi.aw.qos) 
        
        # lenRem, actualAddr logic
        Switch(st)\
        .Case(st_t.fullIdle,
            c(self.DATA_LEN, lenRem), 
            c(baseAddr, actualAddr)
        ).Case(st_t.writeAddr,
            If(axi.aw.ready,
                If(lenRem > self.MAX_BUTST_LEN,
                   c(actualAddr+self.MAX_BUTST_LEN, actualAddr),
                   c(lenRem - self.MAX_BUTST_LEN, lenRem)
                ).Else(
                   c(actualAddr+lenRem, actualAddr),
                   c(0, lenRem)
                )
            ).Else(
               actualAddr._same(),
               lenRem._same()
            )
        ).Default(
            actualAddr._same(),
            lenRem._same()
        )
        
    def connectRegisters(self, st, onoff, baseAddr):
        """
        connection of axilite registers
        """
        idle = st._eq(st._dtype.fullIdle)
        regs = self.regsConventor
        c(Concat(onoff, idle._convert(BIT), vec(0, self.DATA_WIDTH - 2)),
             regs.control_in)
        
        If(regs.control_out.vld,
           c(regs.control_out.data[0], onoff)
        ).Else(
           onoff._same()
        )
        
        c(baseAddr, regs.baseAddr_in)
        If(regs.baseAddr_out.vld,
           c(regs.baseAddr_out.data, baseAddr)
        ).Else(
           baseAddr._same()
        )  
    
    def mainFsm(self, st, onoff, lenRem, actualLenRem):
        axi = self.axi
        st_t = st._dtype
        
        w_ackAll = self.w_allAck(st)
        
        Switch(st)\
        .Case(st_t.fullIdle,
            If(onoff,
                c(st_t.writeAddr)
            ).Else(
                st._same()
            )
        ).Case(st_t.writeAddr,
            If(axi.aw.ready,
                If(lenRem._eq(1),
                   c(st_t.writeDataLast, st)
                ).Else(
                   c(st_t.writeData, st)
                )
            ).Else(
                st._same()
            )
        ).Case(st_t.writeData,
            If(w_ackAll & (actualLenRem._eq(2)),
               c(st_t.writeDataLast, st)
            ).Else(
               st._same()
            )
        ).Case(st_t.writeDataLast,
            If(w_ackAll,
                If(lenRem != 0,
                   c(st_t.writeAddr, st)
                ).Else(
                   c(st_t.fullIdle, st)
                )
            ).Else(
                st._same()
            )
        )
    
    def w_allAck(self, st):
        """
        In this clk data word will be transfered
        """
        st_t = st._dtype
        w_en = st._eq(st_t.writeData) | st._eq(st_t.writeDataLast)
        return w_en & self.dataIn.vld & self.axi.w.ready 
    
    def dataWFeed(self, st, lenRem, actualLenRem):
        """
        Connection between din and axi.w channel
        """
        w = self.axi.w
        din = self.dataIn
        st_t = st._dtype
        
        last = st._eq(st_t.writeDataLast)
        w_en = st._eq(st_t.writeData) | last
        
        c(din.vld & w_en, w.valid)
        c(din.data, w.data)
        c(0, w.id)
        c(Bitmask.mask(w.strb._dtype.bit_length()), w.strb)
        c(last, w.last)
        
        c(w_en & w.ready, din.rd)
        
        w_allAck = self.w_allAck(st)
        
        # actualLenRem driver
        Switch(st)\
        .Case(st_t.writeData,
                If(w_allAck,
                    c(actualLenRem - 1, actualLenRem)
                ).Else(
                    actualLenRem._same()
                )
        ).Case(st_t.writeDataLast,
                If(w_allAck,
                   c(0, actualLenRem)
                ).Else(
                   actualLenRem._same()
                )
        ).Default(
            If(lenRem > self.MAX_BUTST_LEN,
               c(self.MAX_BUTST_LEN, actualLenRem)
            ).Else(
               c(lenRem[actualLenRem._dtype.bit_length():], actualLenRem)
            )
        )
        
        
    def _impl(self):
        propagateClkRstn(self)
        c(self.cntrl, self.regsConventor.axi)
        axi = self.axi
        
        # disable read channel
        c(0, *where(axi.ar._interfaces, lambda x: x is not axi.ar.ready))    
        c(0, axi.r.ready)
        
        c(1, axi.b.ready)  # we do ignore write confirmations
        
        st_t = Enum("state_type", ["fullIdle", "writeAddr", "writeData", "writeDataLast"])

        onoff = self._reg("on_off_reg", defVal=0)
        baseAddr = self._reg("baseAddr_reg", vecT(self.ADDR_WIDTH), 0)
        st = self._reg("state_reg", st_t, st_t.fullIdle)
        actualAddr = self._reg("actualAddr_reg", vecT(self.ADDR_WIDTH))
        lenRem = self._reg("lenRem_reg", vecT(evalParam(self.DATA_LEN).val.bit_length() + 1),
                            self.DATA_LEN)
        actualLenRem = self._reg("actualLenRem_reg", axi.aw.len._dtype)

        self.connectRegisters(st, onoff, baseAddr)
        self.axiWAddrHandler(st, baseAddr, actualAddr, lenRem)
        self.mainFsm(st, onoff, lenRem, actualLenRem)
        self.dataWFeed(st, lenRem, actualLenRem)
        
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = Axi4streamToMem()
    #u = AxiLiteRegs(Axi4streamToMem().REGISTER_MAP)
    print(toRtl(u))
    
