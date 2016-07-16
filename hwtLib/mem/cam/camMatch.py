from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil
from hdl_toolkit.interfaces.std import Handshaked, VldSynced
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import connect
from hdl_toolkit.hdlObjects.typeShortcuts import vecT

from hwtLib.mem.cam.interfaces import DataWithMatch
from hwtLib.mem.cam.camWrite import mkCounter
from hwtLib.logic.dec_en import DecEn

c = connect

class CamMatch(Unit):
    def _config(self):
        self.COLUMNS = Param(1)
        self.ROWS = Param(1)
        self.CELL_WIDTH = Param(1)
        self.CELL_HEIGHT = Param(1)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.storage = DataWithMatch()
            
            self.din = Handshaked()
            self.din.DATA_WIDTH.set(self.COLUMNS * self.CELL_WIDTH)
            
            self.outMatch = VldSynced()
            self.outMatch.DATA_WIDTH.set(self.ROWS * self.CELL_HEIGHT)
            
            
            self.match_enable_decoder = DecEn()
            self.match_enable_decoder.DATA_WIDTH.set(self.CELL_HEIGHT)
    
    def _impl(self):
        din = self.din
        storage = self.storage
        CELL_HEIGHT = self.CELL_HEIGHT
        CELL_WIDTH = self.CELL_WIDTH
                
        inreg_we = self._sig("inreg_we")
        match_we = self._sig("match_we", vecT(CELL_HEIGHT))
        data_reg = self._reg("data_reg", self.din.data._dtype)
        out_rdy_register = self._reg("out_rdy_register", defVal=0)
        
        # input_regs
        If(inreg_we,
           c(din.data, data_reg)
           ,
           c(data_reg, data_reg)
        )

        me_reg = self._sig("me_reg", defVal=0)
        # input_me_reg
        c(inreg_we, me_reg)
        
        # real_counter_gen
        CH = evalParam(CELL_HEIGHT).val
        if CH == 1:
            counter_busy = False
            counter_last = me_reg
            counter_ce = me_reg
            input_rdy = True
            counter = 0
        elif CH > 1:
            #real_counter_gen 
            counter_ce = self._sig("counter_ce")
            counter, counter_busy, counter_last = mkCounter(
                            self,"counter", counter_ce, vecT(log2ceil(CELL_HEIGHT))
                            )
            c(me_reg | counter_busy, counter_ce) 
            input_rdy = (~counter_busy | counter_last) & ~me_reg
        else:
            raise NotImplementedError()
        c(input_rdy, din.rd)
        c(din.vld & input_rdy, inreg_we)
        
        
        # cam_match_gen :
        CH = evalParam(CELL_HEIGHT).val
        for i in range(evalParam(self.COLUMNS).val):
            dr = data_reg[CELL_WIDTH*(i+1):(CELL_WIDTH*i)]
            c(dr, storage.data[(CELL_WIDTH+i*6):(i*6)]) 
            # bank_data_gen
            if CH > 1:
                c(counter, storage.data[((i+1)*6):CELL_WIDTH+i*6]) 
        c(counter_ce, storage.vld)
        
        #match_words_reg_gen
        for i in range(evalParam(CELL_HEIGHT).val):
            #match_bits_reg_gen
            for j in range(evalParam(self.ROWS).val):
                #match_reg
                If(self.clk._onRisingEdge(),
                    If(match_we[i],
                      c(storage.match[j], self.outMatch.data[CELL_HEIGHT*j+i] )
                    )
                )
                
        med = self.match_enable_decoder
        c(counter, med.din)
        c(counter_ce, med.en)
        c(med.dout, match_we)
        
        # out_rdy_register
        orr = out_rdy_register
        c(counter_last, orr)
        c(orr, self.outMatch.vld)

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(CamMatch))
        
        