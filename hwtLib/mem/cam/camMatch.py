from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil
from hdl_toolkit.interfaces.std import Ap_hs, Ap_vld
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import connect
from hdl_toolkit.hdlObjects.typeShortcuts import vecT

from hwtLib.mem.cam.interfaces import DataWithMatch
from hwtLib.mem.cam.camWrite import mkCounter

c = connect

class CamMatch(Unit):
    def _config(self):
        self.COLUMNS = Param(1)
        self.ROWS = Param(1)
        self.CELL_WIDTH = Param(1)
        self.CELL_HEIGHT = Param(1)
    
    def _declr(self):
        addClkRstn(self)
        
        self.dIn = Ap_hs()
        self.dIn.DATA_WIDTH.set(self.COLUMNS * self.CELL_WIDTH)
        
        self.outMatch = Ap_vld()
        self.outMatch.DATA_WIDTH.set(self.ROWS * self.CELL_HEIGHT)
        
        self.storage = DataWithMatch()
        
        self._shareAllParams()
        self._mkIntfExtern()
    
    def _impl(self):
        dIn = self.dIn
        storage = self.storage
        CELL_HEIGHT = self.CELL_HEIGHT
        CELL_WIDTH = self.CELL_WIDTH
                
        inreg_we = self._sig("inreg_we")
        
        data_reg = self._reg("data_reg", self.dIn.data._dtype)
        # input_regs
        If(inreg_we,
           c(dIn.data, data_reg)
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
        
        # cam_match_gen :
        CH = evalParam(CELL_HEIGHT).val
        for i in range(evalParam(self.COLUMNS).val):
            dr = data_reg[CELL_WIDTH*(i+1):(CELL_WIDTH*i)]
            c(dr, storage.data[(CELL_WIDTH*i*6):(i*6)]) 
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
                      c(storage.match[j], self.outMatch.data[j*CELL_HEIGHT+i] )
                    )
                )