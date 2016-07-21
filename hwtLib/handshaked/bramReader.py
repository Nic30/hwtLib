from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.std import BramPort_withoutClk, Handshaked, \
    HandshakeSync
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.synthetisator.codeOps import c, Switch, If

class HsBramPortReader(Unit):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(32)
        
        self.ADDR_LOW = Param(0)
        self.SIZE = Param(255)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            # start reading data over dataOut
            self.en = HandshakeSync()
            
            # delete active memoryset
            self.clean = HandshakeSync()
            
            with self._paramsShared():
                self.dataIn = BramPort_withoutClk()
                self.dataOut = Handshaked() 
    
    def fsm(self, st, data_flag, data_inReg, addr):
        st_t = st._dtype
        Out = self.dataOut
        
        def onLastGoIddle():
            ADDR_HIGH = self.ADDR_LOW + self.SIZE - 1
            lastAddr = addr._eq(ADDR_HIGH)
            return  If(lastAddr,
                        c(st_t.iddle, st)
                    ).Else(
                        st._same()
                    )
        
        Switch(st)\
        .Case(st_t.iddle,
                If(self.en.vld,
                    c(st_t.sendingData, st)
                ).Elif(self.clean.vld,
                    c(st_t.inCleaning, st)
                ).Else(
                    st._same()
                )
        ).Case(st_t.sendingData,
                If(data_inReg | (data_flag & ~Out.rd),
                    # if some data is loaded and it can not be send out
                    st._same()
                ).Else(
                    # if is possible to send data in this clk
                    onLastGoIddle()
                )
        ).Case(st_t.inCleaning,
                onLastGoIddle()
        )
                
    def _impl(self):
        In = self.dataIn
        Out = self.dataOut
        
        st_t = Enum("st_t", ["iddle", "sendingData", "inCleaning"])
        self.st = st = self._reg("st_reg", st_t, st_t.iddle)
        addr = self.addr = self._reg("addr_reg", In.addr._dtype)
        data_reg = self.data_reg = self._reg("data_reg", In.dout._dtype)
        data_flag = self.data_flag = self._reg("data_flag_reg", defVal=0)
        data_inReg = self.data_inReg = self._reg("data_inReg_flag_reg", defVal=0)
        
        
        self.fsm(st, data_flag, data_inReg, addr)

        c(st._eq(st_t.iddle), self.en.rd)
        c(st._eq(st_t.iddle), self.clean.rd)
        
        c(data_inReg | data_flag, Out.vld)
        
        c(0, In.din)
        c(1, In.en)
        c(st._eq(st_t.inCleaning), In.we)
        c(addr, In.addr)

        
        If(data_flag,
           c(In.dout, data_reg)
        ).Else(
           data_reg._same()
        )
        If(data_inReg,
           c(data_reg, Out.data)
        ).Else(
           c(In.dout, Out.data)
        )
        
        # addr incrementig logic
        Switch(st)\
        .Case(st_t.iddle,
                c(self.ADDR_LOW, addr)
        ).Case(st_t.sendingData,
            If(data_inReg | (data_flag & ~Out.rd),
                # if some data is loaded and it can not be send out
                addr._same()
            ).Else(
                # if is possible to send data in this clk
                c(addr + 1, addr)
            )
        ).Case(st_t.inCleaning,
             c(addr + 1, addr)
        )
        
        # dataRegs logic
        If(st._eq(st_t.sendingData),
            c(1, data_flag), 
            If(data_inReg | (data_flag & ~Out.rd),
                # if some data is loaded and it can not be send out
                If(data_inReg,
                   c(~Out.rd, data_inReg)
                ).Else(
                   data_inReg._same()
                )
            ).Else(
                # if is possible to send data in this clk
                c(~self.dataOut.rd, data_inReg)
            )
        ).Else(
            c(0, data_flag), 
            c(0, data_inReg) 
        )
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(HsBramPortReader()))        
