import math

from hdl_toolkit.hdlObjects.typeShortcuts import hInt, vec
from hdl_toolkit.interfaces.std import Handshaked, VldSynced
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hdl_toolkit.synthetisator.codeOps import If, c
from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hwtLib.mem.cam.camMatch import CamMatch
from hwtLib.mem.cam.camStorage import CamStorage
from hwtLib.mem.cam.camWrite import CamWrite
from hwtLib.mem.cam.interfaces import AddrDataHs
from hdl_toolkit.synthetisator.shortcuts import synthetizeAndSave


def extend(sig, targetWidth):
    tw = evalParam(targetWidth).val
    aw = sig._dtype.bit_length()
    if tw == aw:
        return sig
    elif aw < tw:
        return sig._concat(vec(0, tw - aw))
    else:
        raise NotImplementedError()
    
def div_up(sig, divider):
    v = sig.staticEval().val
    divider = divider.staticEval().val
    v = math.ceil(v / divider)
    return hInt(int(v)) 


class CamInLUT(Unit):
    """
    CAM where data are store in LUT-RAM
    [TODO]: currently not working
    """
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
        SEQUENCING_FACTOR = self.SEQUENCING_FACTOR
        DATA_WIDTH = self.DATA_WIDTH
        ITEMS = self.ITEMS

        self.CELL_WIDTH = hInt(6) - SEQUENCING_FACTOR;
        self.CELL_HEIGHT = hInt(2) ** SEQUENCING_FACTOR;
        self.COLUMNS = div_up(DATA_WIDTH, self.CELL_WIDTH);
        self.ROWS = div_up(ITEMS, self.CELL_HEIGHT);
        
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.match = Handshaked()
                self.write = AddrDataHs()
            self.out = VldSynced()
            self.out._replaceParam("DATA_WIDTH", self.ITEMS)
        
        with self._paramsShared():
            self.camWrite = CamWrite()
            self.camStorage = CamStorage()
            self.camMatch = CamMatch()
            
            for u in (self.camWrite, self.camStorage, self.camMatch):
                u.COLUMNS.set(self.COLUMNS)
                u.ROWS.set(self.ROWS)
                
            for u in (self.camWrite, self.camMatch):
                u.CELL_WIDTH.set(self.CELL_WIDTH)
                u.CELL_HEIGHT.set(self.CELL_HEIGHT)

    
    def _impl(self):
        COLUMNS = self.COLUMNS
        CELL_WIDTH = self.CELL_WIDTH
        ROWS = self.ROWS
        CELL_HEIGHT = self.CELL_HEIGHT
        DW = COLUMNS * CELL_WIDTH
        
        match = self.match
        write = self.write
        
        mdata_padded = extend(match.data, DW)
        wdata_padded = extend(write.data, DW)
        mask_padded = extend(write.mask,  DW)
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
        c(mdata_padded, m.din.data)
        c(match_req, m.din.vld)
        c(m.din.rd, match_ready_base)
        
        c(m.outMatch.data[self.ITEMS:0], self.out.data)
        c(m.outMatch.vld, self.out.vld)
        
        storage_me = m.storage.vld
        
        # write_i
        w = self.camWrite
        c(wdata_padded, w.din.data)
        c(mask_padded, w.din.mask)
        c(addr_padded, w.din.addr)
        c(write_req, w.din.vld)
        c(w.din.rd, write_ready_base)
        
        # storage_i
        s = self.camStorage
        If(storage_me,
           c(m.storage.data, s.din.addr)
        ).Else(
           c(w.dout.data, s.din.addr)
        )
        c(w.dout.di, s.din.dataIn)
        c(w.dout.we , s.din.we)
        c(storage_me, s.match.rd)
        c(s.match.data, m.storage.match)
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # with open("/home/nic30/Documents/vivado/scriptTest/scriptTest.srcs/sources_1/new/top.vhd", "w") as f:
    u = CamInLUT()
    # print(toRtl(u))
    synthetizeAndSave(u, folderName="/home/nic30/Documents/test_ip_repo/cam/")
    # f.write(s)
