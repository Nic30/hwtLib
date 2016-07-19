from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.std import BramPort_withoutClk, Handshaked, \
    HandshakeSync
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c
from hdl_toolkit.synthetisator.rtlLevel.codeOp import Switch, If

class HsBramPortHeader(Unit):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(32)
        
        self.ADDR_LOW = Param(0)
        self.SIZE = Param(255)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.en = HandshakeSync()
            
            with self._paramsShared():
                self.dataIn = BramPort_withoutClk()
                self.dataOut = Handshaked() 
                
    def _impl(self):
        In = self.dataIn
        Out = self.dataOut
        
        st_t = Enum("st_t", ["iddle", "sendingData"])
        st = self._reg("st_reg", st_t, st_t.iddle)
        addr = self._reg("addr_reg", In.addr._dtype)
        data_reg = self._reg("data_reg", In.dout._dtype)
        data_flag = self._reg("data_flag_reg", defVal=0)
        data_inReg = self._reg("data_inReg_flag_reg", defVal=0)
        
        
        c(st._eq(st_t.iddle), self.en.rd)
        
        c(data_inReg | data_flag, Out.vld)
        

        c(0, In.din)
        c(1, In.en)
        c(0, In.we)
        c(addr, In.addr)
        
        If(data_flag,
           c(In.dout, data_reg)
           ,
           data_reg._same()
        )
        If(data_inReg,
           c(data_reg, Out.data)
           ,
           c(In.dout, Out.data)
        )
        
        Switch(st,
            (st_t.iddle,
                c(self.ADDR_LOW, addr) + 
                c(0, data_flag) + 
                c(0, data_inReg) + 
                If(self.en.vld,
                   c(st_t.sendingData, st)
                   ,
                   st._same()
                )
            ),
            (st_t.sendingData,
                c(1, data_flag) +
                If(data_inReg | (data_flag & ~Out.rd),
                    # if some data is loaded and it can not be send out
                    addr._same()+
                    If(data_inReg,
                       c(~Out.rd, data_inReg)
                       ,
                       data_inReg._same()
                    )
                    ,
                    # if is possible to send data in this clk
                    c(~self.dataOut.rd, data_inReg) +
                    If(addr._eq(self.ADDR_LOW + self.SIZE),
                        c(self.ADDR_LOW, addr)
                        ,
                        c(addr + 1, addr)
                    )
                )
            
            )
        )
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(HsBramPortHeader()))        
