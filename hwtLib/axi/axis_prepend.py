from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.interfaces.amba import AxiStream_withoutSTRB
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.synthetisator.rtlLevel.codeOp import Switch, If
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c
from hdl_toolkit.synthetisator.shortcuts import toRtl
from hdl_toolkit.hdlObjects.typeShortcuts import hBit, vec
from hdl_toolkit.bitmask import Bitmask
from hdl_toolkit.hdlObjects.specialValues import DIRECTION
from hdl_toolkit.interfaces.utils import addClkRstn
from hwtLib.axi.axis_compBase import AxiSCompBase


class AxiSPrepend(AxiSCompBase):
    """
    AXI-Stream Prepend
    
    The unit merges two streams BASE and PREP. The PREP
    stream is prepended before BASE.
    
    Both streams are merged into a single frame (masking
    TLAST bit of PREP stream). However, this feature
    may be turned off by setting MASK_LAST to false.
    
    Data are bypassed as they come if possible.
    """
        
    def _config(self):
        super()._config()
        self.MASK_LAST = Param(True)
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.base = self.intfCls()
                self.prep = self.intfCls()
                self.out =  self.intfCls()
        
    def _impl(self):
        stT = Enum('t_state', ["prep", "base"])
        st = self._reg('st', stT, stT.prep)
        useStrb = hasattr(self.prep, 'strb')
        prep = self.prep
        base = self.base
        out = self.out
        MASK_LAST = self.MASK_LAST
        vld = self.getVld 
        rd = self.getRd
        
        Switch(st,
            (stT.prep,
                If(vld(prep) & prep.last & rd(out),
                   c(stT.base, st)
                   ,
                   st._same()
                )
            ),
            (stT.base,
                If(vld(base) & base.last & rd(out),
                    c(stT.prep, st)
                    ,
                    st._same()
                )
            )
        )
        
        prepLast = MASK_LAST._ternary(hBit(0), prep.last)
        if useStrb:
            strbW = self.prep.strb._dtype.bit_length()
            prepStrb = MASK_LAST._ternary(vec(Bitmask.mask(strbW), strbW), prep.strb)
        
        for bi, pi, oi in zip(self.base._interfaces, self.prep._interfaces, self.out._interfaces):
            if useStrb and oi is self.out.strb:
                pi = prepStrb
            elif oi == self.out.last:
                pi = prepLast
            
            if oi._masterDir == DIRECTION.IN:
                # swap because direction is oposite
                c(oi & st._eq(stT.prep), pi)
                c(oi & st._eq(stT.base), bi)
            else:
                If(st._eq(stT.prep),
                    c(pi, oi),
                    c(bi, oi)
                )

if __name__ == "__main__":
    u = AxiSPrepend(AxiStream_withoutSTRB)
    print(toRtl(u))
