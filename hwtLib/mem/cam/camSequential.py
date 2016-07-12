import math

from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hdl_toolkit.interfaces.std import Ap_hs, Ap_vld
from hdl_toolkit.hdlObjects.typeShortcuts import hInt, vec

from hwtLib.mem.cam.interfaces import AddrDataHs
from hwtLib.mem.cam.camWrite import CamWrite
from hwtLib.mem.cam.camStorage import CamStorage
from hwtLib.mem.cam.camMatch import CamMatch
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If

def extend(sig, targetWidth):
    tw = evalParam(targetWidth).val
    aw = sig._dtype.bit_length()
    if tw == aw:
        return sig
    elif aw < tw:
        raise sig._concat(vec(0, tw - aw))
    else:
        raise NotImplementedError()
    
def div_up(sig, divider):
    v = sig.staticEval().val
    divider = divider.staticEval().val
    v = math.ceil(v / divider)
    return hInt(int(v)) 

class CamSequential(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(36)
        self.ITEMS = Param(16)
        # Value of matching Sequencing Factor (SF).
        # Must be in range 0-6.
        # Duration of every match is 2^SF cycles.
        # Duration of every item write is 2^(6-SF) cycles.
        # One 7Series 6-LUT can store 2^SF elements (CAM cell height) of (6-SF) bits (CAM cell width).
        # SHORT: Higher SF means fewer FPGA resources but lower throughtput of matching.
        self.SEQUENCING_FACTOR = Param(0)
        
        
        # What to do when write and match are both requested in the same cycle?
        # true = write has higher priority
        # false = read has higher priority
        self.WRITE_BEFORE_MATCH = Param(False)
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.match = Ap_hs()
            self.write = AddrDataHs()

        self.camWrite = CamWrite()
        self.camStorage = CamStorage()
        self.camMatch = CamMatch()


        SEQUENCING_FACTOR = self.SEQUENCING_FACTOR
        DATA_WIDTH = self.DATA_WIDTH
        ITEMS = self.ITEMS

        
        self.CELL_WIDTH = hInt(6) - SEQUENCING_FACTOR;
        self.CELL_HEIGHT = hInt(2) ** SEQUENCING_FACTOR;
        self.COLUMNS = div_up(DATA_WIDTH, self.CELL_WIDTH);
        self.ROWS = div_up(ITEMS, self.CELL_HEIGHT);
        
        for u in (self.camWrite, self.camStorage, self.camMatch):
            u.COLUMNS.set(self.COLUMNS)
            u.ROWS.set(self.ROWS)
            
        for u in (self.camWrite,self.camMatch):
            u.CELL_WIDTH.set(self.CELL_WIDTH)
            u.CELL_HEIGHT.set(self.CELL_HEIGHT)
        
        self._shareAllParams()
    
        self.out = Ap_vld(isExtern=True)
        self.out._replaceParam("DATA_WIDTH", self.ITEMS)
    
    def _impl(self):
        COLUMNS = self.COLUMNS
        CELL_WIDTH = self.CELL_WIDTH
        ROWS = self.ROWS
        CELL_HEIGHT = self.CELL_HEIGHT
        
        match = self.match
        write = self.write
        
        mdata_padded = extend(match.data, COLUMNS * CELL_WIDTH)
        wdata_padded = extend(write.data, COLUMNS * CELL_WIDTH)
        mask_padded = extend(write.mask, COLUMNS * CELL_WIDTH)
        addr_padded = extend(write.addr, log2ceil(ROWS * CELL_HEIGHT))
        write_ready_base = self._sig("write_ready_base")
        match_ready_base = self._sig("match_ready_base")
        
        propagateClkRstn(self)
        
        # write_first_gen
        if evalParam(self.WRITE_BEFORE_MATCH).val:
            match_req = match.vld & write_ready_base & ~write.vld
            write_req = write.vld & match_ready_base
            mr = match_ready_base & write_ready_base & ~write.vld 
            wr = write_ready_base & match_ready_base
        # match_first_gen 
        else:
            match_req = match.vld & write_ready_base
            write_req = write.vld & match_ready_base & ~match.vld
            mr = match_ready_base & write_ready_base
            wr = write_ready_base & match_ready_base & ~match.vld
        
        c(mr, match.rd)
        c(wr, write.rd)
        
        # match_i
        m = self.camMatch
        c(mdata_padded, m.dIn.data)
        c(match_req, m.dIn.vld)
        c(m.dIn.rd, match_ready_base)
        
        c(m.outMatch.data[self.ITEMS:0], self.out.data)
        c(m.outMatch.vld, self.out.vld)
        
        storage_mdata = m.storage.data
        storage_me = m.storage.vld
        
        # write_i
        w = self.camWrite
        c(wdata_padded, w.dIn.data)
        c(mask_padded, w.dIn.mask)
        c(addr_padded, w.dIn.addr)
        c(write_req, w.dIn.vld)
        c(w.dIn.rd, write_ready_base)
        storage_wdata = w.dOut.data
        storage_di = w.dOut.di
        storage_we = w.dOut.we          
        
        # storage_i
        s = self.camStorage
        If(storage_me,
           c(storage_mdata, s.dIn.data)
           ,
           c(storage_wdata, s.dIn.data)
        )
        c(storage_di, s.dIn.di)
        c(storage_we, s.dIn.we)
        c(storage_me, s.match.rd)
        c(s.match.data, m.storage.match)
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    with open("/home/nic30/Documents/vivado/scriptTest/scriptTest.srcs/sources_1/new/top.vhd", "w") as f:
        s= toRtl(CamSequential)
        f.write(s)
        print(s)