import math

from hdl_toolkit.hdlObjects.typeShortcuts import hInt, vec
from hdl_toolkit.interfaces.std import Handshaked, VldSynced
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hdl_toolkit.synthesizer.codeOps import If, Concat, power
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
from hwtLib.mem.cam.camMatch import CamMatch
from hwtLib.mem.cam.camStorage import CamStorage
from hwtLib.mem.cam.camWrite import CamWrite
from hwtLib.mem.cam.interfaces import AddrDataHs


def extend(sig, targetWidth):
    tw = evalParam(targetWidth).val
    aw = sig._dtype.bit_length()
    if tw == aw:
        return sig
    elif aw < tw:
        return Concat(sig, vec(0, tw - aw))
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

        self.CELL_WIDTH = hInt(6) - SEQUENCING_FACTOR
        self.CELL_HEIGHT = power(2, SEQUENCING_FACTOR)
        self.COLUMNS = div_up(DATA_WIDTH, self.CELL_WIDTH)
        self.ROWS = div_up(ITEMS, self.CELL_HEIGHT)
        
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
        mask_padded = extend(write.mask, DW)
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
        
        match.rd ** mr 
        write.rd ** wr 
        
        # match_i
        m = self.camMatch
        m.din.data ** mdata_padded
        m.din.vld ** match_req
        match_ready_base ** m.din.rd
        
        self.out.data ** m.outMatch.data[self.ITEMS:0] 
        self.out.vld ** m.outMatch.vld 
        
        storage_me = m.storage.vld
        
        # write_i
        w = self.camWrite
        w.din.data ** wdata_padded 
        w.din.mask ** mask_padded 
        w.din.addr ** addr_padded 
        w.din.vld ** write_req 
        write_ready_base ** w.din.rd 
        
        # storage_i
        s = self.camStorage
        If(storage_me,
           s.din.addr ** m.storage.data 
        ).Else(
           s.din.addr ** w.dout.data 
        )
        s.din.dataIn ** w.dout.di 
        s.din.we ** w.dout.we 
        s.match.rd ** storage_me 
        m.storage.match ** s.match.data 
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl, toRtlAndSave
    u = CamInLUT()
    print(toRtl(u))
    #toRtlAndSave(u, folderName="/home/nic30/Documents/test_ip_repo/cam/")
    # f.write(s)
