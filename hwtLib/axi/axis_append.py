
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.hdlObjects.specialValues import DIRECTION
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.synthetisator.param import Param, evalParam
from hwtLib.axi.axis_compBase import AxiSCompBase
from hdl_toolkit.synthetisator.codeOps import Switch, If, c


class AxiSAppend(AxiSCompBase):
    """
    AXI-Stream Append
    
    Behind frame from dataIn0 is appended data from dataIn1.
    If JOIN is set frames are merged. 
    No data alignment is performed.
    """
    def _config(self):
        super()._config()
        self.JOIN = Param(True)
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.dataIn0 = self.intfCls()
                self.dataIn1 = self.intfCls()
                self.dataOut = self.intfCls()
        
    def _impl(self):
        stT = Enum('t_state', ["sendDataIn0", "sendDataIn1"])
        st = self._reg('st', stT, stT.sendDataIn0)
        In0 = self.dataIn0
        In1 = self.dataIn1
        out = self.dataOut
        vld = self.getVld 
        rd = self.getRd
        
        Switch(st)\
        .Case(stT.sendDataIn0,
            If(vld(In0) & In0.last & rd(out),
               c(stT.sendDataIn1, st)
            ).Else(
               st._same()
            )
        ).Case(stT.sendDataIn1,
            If(vld(In1) & In1.last & rd(out),
                c(stT.sendDataIn0, st)
            ).Else(
                st._same()
            )
        )
        doJoin = evalParam(self.JOIN).val
        i = lambda intf: intf._interfaces
        for i0, i1, oi in zip(i(self.dataIn0), 
                              i(self.dataIn1),
                              i(self.dataOut)):
            if oi._masterDir == DIRECTION.IN:
                # swap because direction is oposite
                c(oi & st._eq(stT.sendDataIn0), i0)
                c(oi & st._eq(stT.sendDataIn1), i1)
            else:
                if oi._name == "last" and doJoin:
                    i0 = 0
                If(st._eq(stT.sendDataIn0),
                    c(i0, oi),
                ).Else(
                    c(i1, oi)
                )

if __name__ == "__main__":
    from hdl_toolkit.interfaces.amba import AxiStream_withoutSTRB
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = AxiSAppend(AxiStream_withoutSTRB)
    print(toRtl(u))
