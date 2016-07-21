from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil

from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hInt
from hdl_toolkit.synthetisator.codeOps import If, c

from hwtLib.mem.cam.interfaces import AddrDataHs, CamWritterPort
from hwtLib.logic.dec_en import DecEn


def mkCounter(unit, name, counter_ce, dType):
    counter = unit._reg(name, dType, 0)
    busy = counter != 0 ;
    last = counter._eq(dType.all_mask())
    # counter_i
    If(counter_ce,
      c(counter + 1, counter)
    ).Else(
      c(counter, counter)
    )
    return counter, busy, last

class CamWrite(Unit):
    def _config(self):
        self.COLUMNS = Param(8)
        self.ROWS = Param(16)
        self.CELL_WIDTH = Param(6)
        self.CELL_HEIGHT = Param(1)

    def _declr(self):
        assert evalParam(self.CELL_WIDTH).val <=6
        with self._asExtern():
            addClkRstn(self)
            
            self.din = AddrDataHs()
            self.din.DATA_WIDTH.set(self.COLUMNS * self.CELL_WIDTH)
            self.din.ADDR_WIDTH.set(log2ceil(self.ROWS*self.CELL_HEIGHT))
            
            self.dout = CamWritterPort()
            self.dout._updateParamsFrom(self)
        self.write_enable_decoder = DecEn()
        self.write_enable_decoder.DATA_WIDTH.set(self.ROWS)
        
    def _impl(self):
        dIn = self.din
        dout = self.dout
        CELL_WIDTH = self.CELL_WIDTH
        COLUMNS = self.COLUMNS
        r = self._reg
        
        counter_ce = self._sig("counter_ce")
        counter, counter_busy, counter_last = mkCounter(self,"counter", counter_ce, vecT(CELL_WIDTH))
        
        wr_reg = r("wr_reg", defVal=0)
        data_reg = r("data_reg", dIn.data._dtype, defVal=0)
        mask_reg = r("mask_reg", dIn.mask._dtype, defVal=0)
        addr_reg = r("addr_reg", dIn.addr._dtype, defVal=0)
        data_addr = self._sig("data_addr", vecT(6), 0) 
        

        c(wr_reg | counter_busy, counter_ce)
        input_rdy = (~counter_busy | counter_last) & ~wr_reg;
        inreg_we = self.din.vld & input_rdy   
        c(input_rdy, self.din.rd)

        # input_regs
        If(inreg_we, 
           c(dIn.data, data_reg),
           c(dIn.mask, mask_reg),
           c(dIn.addr, addr_reg)
        ).Else( 
           # this branch is not necessary 
           data_reg._same(),
           mask_reg._same(),
           addr_reg._same()
        )
        # input_wr_reg
        c(wr_reg, wr_reg)
        
        # real_row_addr_gen
        if evalParam(self.ROWS).val > 1:
            row_addr = addr_reg[:(hInt(6)-CELL_WIDTH)]
        else:
            raise NotImplementedError()
        
        
        # real_bank_addr_gen
        if evalParam(CELL_WIDTH).val < 6:
            bank_addr = addr_reg[6-CELL_WIDTH:0]
            c(bank_addr, data_addr[6:CELL_WIDTH]);
        
        c(counter, data_addr[CELL_WIDTH:0])

        # cam_wr_gen
        for i in range(evalParam(COLUMNS).val):
            c(data_addr, dout.data[(i+1)*6:i*6])
            masked_counter =  counter & mask_reg[(CELL_WIDTH*(i+1)):(CELL_WIDTH*i)]
            dr = data_reg[CELL_WIDTH*(i+1):CELL_WIDTH*i]
            c(masked_counter._eq(dr), dout.di[i])

        wec = self.write_enable_decoder
        c(row_addr, wec.din)
        c(counter_ce, wec.en)
        c(wec.dout, dout.we)
        
        c(counter_ce, dout.vld)
        # OUT_WR <= counter_ce;

        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(CamWrite))