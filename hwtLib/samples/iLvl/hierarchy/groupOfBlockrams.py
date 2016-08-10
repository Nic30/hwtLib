from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import Param, Unit, c
from hwtLib.mem.ram import Ram_dp


class GroupOfBlockrams(Unit):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(64)
    
    def _declr(self):
        with self._paramsShared():
            extData = lambda : Signal(dtype=vecT(self.DATA_WIDTH), isExtern=True)
            self.bramR = Ram_dp()
            self.bramW = Ram_dp()
            
            self.ap_clk = Signal(isExtern=True)
            self.we = Signal(isExtern=True)
            self.addr = Signal(dtype=vecT(self.ADDR_WIDTH), isExtern=True)
            self.in_w_a = extData()
            self.in_w_b = extData()
            self.in_r_a = extData()
            self.in_r_b = extData()
            
            self.out_w_a =extData()
            self.out_w_b =extData()
            self.out_r_a =extData()
            self.out_r_b =extData()
    
    def _impl(self):
        s = self
        bramR = s.bramR
        bramW = s.bramW
        
        c(s.ap_clk,
            bramR.a.clk, bramR.b.clk,
            bramW.a.clk, bramW.b.clk)
        c(s.we,
            bramR.a.we, bramR.b.we,
            bramW.a.we, bramW.b.we)
        c(self.addr,
            bramR.a.addr, bramR.b.addr,
            bramW.a.addr, bramW.b.addr)
        
        c(s.in_w_a, bramW.a.din)
        c(s.in_w_b, bramW.b.din)
        c(s.in_r_a, bramR.a.din)
        c(s.in_r_b, bramR.b.din)
        c(bramW.a.dout, s.out_w_a)
        c(bramW.b.dout, s.out_w_b)
        c(bramR.a.dout, s.out_r_a)
        c(bramR.b.dout, s.out_r_b)
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(GroupOfBlockrams))
