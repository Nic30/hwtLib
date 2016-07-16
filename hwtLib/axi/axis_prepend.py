from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
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

class AxisPrepend(Unit):
    """
    AXI-Stream Prepend
    
    The unit merges two streams BASE and PREP. The PREP
    stream is prepended before BASE.
    
    Both streams are merged into a single frame (masking
    TLAST bit of PREP stream). However, this feature
    may be turned off by setting C_MASK_LAST to false.
    
    Data are bypassed as they come if possible.
    """
    def __init__(self, axiIntfCls):
        """
        @param axiIntfCls: class of interface which should be used as interface of this unit
        """
        assert(issubclass(axiIntfCls, AxiStream_withoutSTRB))
        self.axiIntfCls = axiIntfCls
        super().__init__()
        
    def _config(self):
        self.axiIntfCls._config(self) # use same params as interface has
        self.MASK_LAST = Param(True)
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.base = self.axiIntfCls()
                self.prep = self.axiIntfCls()
                self.out = self.axiIntfCls()
        
    def _impl(self):
        stT = Enum('t_state', ["prep", "base"])
        st = self._reg('st', stT, stT.prep)
        useStrb = hasattr(self.prep, 'strb')
        prep = self.prep
        base = self.base
        out = self.out
        
        Switch(st,
                (stT.prep,
                    If(prep.valid & prep.last & out.ready,
                       c(stT.base, st)
                       ,
                       c(st, st)
                    )
                ),
                (stT.base,
                    If(base.valid & base.last & out.ready,
                        c(stT.prep, st)
                        ,
                        c(st, st)
                    )
                )
        )
        
        prepLast = self.MASK_LAST._ternary(hBit(0), prep.last)
        if useStrb:
            strbW = self.prep.strb._dtype.bit_length()
            prepStrb = self.MASK_LAST._ternary(vec(Bitmask.mask(strbW), strbW), prep.strb)
        
        for bi, pi, oi in zip(self.base._interfaces, self.prep._interfaces, self.out._interfaces):
            if useStrb and oi == self.out.strb:
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
    u = AxisPrepend(AxiStream_withoutSTRB)
    print(toRtl(u))
