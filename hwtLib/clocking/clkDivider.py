from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.std import Clk, Rst_n
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.codeOps import If, c


class ClkDiv3(Unit):
    """
    @attention: this clock divider implementation suits well for generating of output clock
                inside fpga you should use clocking primitives
                (http://www.xilinx.com/support/documentation/ip_documentation/clk_wiz/v5_1/pg065-clk-wiz.pdf)
    """
    def _declr(self):
        with self._asExtern():
            self.clk = Clk()
            self.rst_n = Rst_n()
    
            self.clkOut = Clk()
    
    def _impl(self):
        r_cnt = self._cntx.sig("r_cnt", typ=vecT(2))    
        f_cnt = self._cntx.sig("f_cnt", typ=vecT(2))    
        rise = self._cntx.sig("rise")
        fall = self._cntx.sig("fall")
        
        rst = self.rst_n._isOn()
        If(rst,
           c(0, r_cnt),
           c(1, rise),
           c(2, f_cnt),
           c(1, fall)
        ).Else(
            If(self.clk._onRisingEdge(),
                If(r_cnt._eq(2),
                    c(0, r_cnt),
                    c(~rise, rise)
                ).Else(
                    c(r_cnt+1, r_cnt),
                )
            ),
            If(self.clk._onFallingEdge(),
                If(f_cnt._eq(2),
                    c(0, f_cnt),
                    c(~fall, fall)
                ).Else(
                    c(f_cnt +1, f_cnt),
                )
            )
        )
        
        c(fall._eq(rise), self.clkOut)

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(ClkDiv3))