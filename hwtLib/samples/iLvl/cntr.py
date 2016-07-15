from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.interfaces.std import Signal, Ap_clk, Ap_rst_n
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import connect
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If


class Cntr(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(2)
        
    def _declr(self):
        with self._asExtern():
            self.clk = Ap_clk()
            self.rst_n = Ap_rst_n()
            self.en = Signal()
            self.val = Signal(dtype=vecT(self.DATA_WIDTH))
        
    def _impl(self):
        reg = self._reg("conter", vecT(self.DATA_WIDTH), 0)
        
        If(self.en,
           connect(reg + 1, reg)
           ,
           connect(reg, reg)
        )
        
        connect(reg, self.val)

