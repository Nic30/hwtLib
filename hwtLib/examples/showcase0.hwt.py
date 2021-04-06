from hwt.code import If, Switch, Concat
from hwt.code_utils import rename_signal
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import INT, SLICE, STR, BIT, FLOAT64
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Signal
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit

class Showcase0(Unit):
    """
        Every HW component class has to be derived from :class:`hwt.synthesizer.unit.Unit` class
    
        .. hwt-autodoc::
        
    """
    def _declr(self):
        # ports
        self.a = Signal(Bits(32, signed=False))
        self.b = Signal(Bits(32, signed=True))
        self.c = Signal(Bits(32))._m()
        self.clk = Signal(Bits(1))
        self.cmp_0 = Signal(Bits(1))._m()
        self.cmp_1 = Signal(Bits(1))._m()
        self.cmp_2 = Signal(Bits(1))._m()
        self.cmp_3 = Signal(Bits(1))._m()
        self.cmp_4 = Signal(Bits(1))._m()
        self.cmp_5 = Signal(Bits(1))._m()
        self.contOut = Signal(Bits(32))._m()
        self.d = Signal(Bits(32))
        self.e = Signal(Bits(1))
        self.f = Signal(Bits(1))._m()
        self.fitted = Signal(Bits(16))._m()
        self.g = Signal(Bits(8))._m()
        self.h = Signal(Bits(8))._m()
        self.i = Signal(Bits(2))
        self.j = Signal(Bits(8))._m()
        self.k = Signal(Bits(32))._m()
        self.out = Signal(Bits(1))._m()
        self.output = Signal(Bits(1))._m()
        self.rst_n = Signal(Bits(1, negated=True))
        self.sc_signal = Signal(Bits(8))._m()
        # component instances

    def _impl(self):
        a, b, c, clk, cmp_0, cmp_1, cmp_2, cmp_3, cmp_4, cmp_5, contOut, \
        d, e, f, fitted, g, h, i, j, k, out, \
        output, rst_n, sc_signal = \
        self.a, self.b, self.c, self.clk, self.cmp_0, self.cmp_1, self.cmp_2, self.cmp_3, self.cmp_4, self.cmp_5, self.contOut, \
        self.d, self.e, self.f, self.fitted, self.g, self.h, self.i, self.j, self.k, self.out, \
        self.output, self.rst_n, self.sc_signal
        # internal signals
        const_private_signal = Bits(32, signed=False).from_py(123)
        fallingEdgeRam = self._sig("fallingEdgeRam", Bits(8, signed=True)[4], def_val=None)
        r = self._sig("r", Bits(1), def_val=0)
        r_0 = self._sig("r_0", Bits(2), def_val=0)
        r_1 = self._sig("r_1", Bits(2), def_val=0)
        r_next = self._sig("r_next", Bits(1), def_val=None)
        r_next_0 = self._sig("r_next_0", Bits(2), def_val=None)
        r_next_1 = self._sig("r_next_1", Bits(2), def_val=None)
        rom = Bits(8, signed=False)[4].from_py({0: 0,
            1: 1,
            2: 2,
            3: 3
        })
        # assig_process_c
        c((a + b._reinterpret_cast(Bits(32, signed=False)))._reinterpret_cast(Bits(32)))
        # assig_process_cmp_0
        cmp_0(a < 4)
        # assig_process_cmp_1
        cmp_1(a > 4)
        # assig_process_cmp_2
        cmp_2(b <= 4)
        # assig_process_cmp_3
        cmp_3(b >= 4)
        # assig_process_cmp_4
        cmp_4(b != 4)
        # assig_process_cmp_5
        cmp_5(b._eq(4))
        # assig_process_contOut
        contOut(const_private_signal._reinterpret_cast(Bits(32)))
        # assig_process_f
        f(r)
        # assig_process_fallingEdgeRam
        If(clk._onFallingEdge(),
            fallingEdgeRam[r_1](a[8:0]._reinterpret_cast(Bits(8, signed=True))),
            k(Concat(Bits(24).from_py(0), fallingEdgeRam[r_1]._reinterpret_cast(Bits(8, signed=False))._reinterpret_cast(Bits(8))))
        )
        # assig_process_fitted
        fitted(a[16:0]._reinterpret_cast(Bits(16)))
        # assig_process_g
        g(Concat(Concat(a[1] & b[1], a[0] ^ b[0] | a[1]), a[6:0]._reinterpret_cast(Bits(6))))
        # assig_process_h
        If(a[2]._eq(1),
            If(r._eq(1),
                h(0)
            ).Elif(a[1]._eq(1),
                h(1)
            ).Else(
                h(2)
            )
        )
        # assig_process_j
        If(clk._onRisingEdge(),
            j(rom[r_1]._reinterpret_cast(Bits(8)))
        )
        # assig_process_out
        out(0)
        # assig_process_output
        output(None)
        # assig_process_r
        If(clk._onRisingEdge(),
            If(rst_n._eq(0),
                r_1(0),
                r_0(0),
                r(0)
            ).Else(
                r_1(r_next_1),
                r_0(r_next_0),
                r(r_next)
            )
        )
        # assig_process_r_next
        r_next_0(i)
        # assig_process_r_next_0
        r_next_1(r_0)
        # assig_process_r_next_1
        If((~r)._eq(1),
            r_next(e)
        ).Else(
            r_next(r)
        )
        # assig_process_sc_signal
        Switch(a)\
            .Case(1,
                sc_signal(0))\
            .Case(2,
                sc_signal(1))\
            .Case(3,
                sc_signal(3))\
            .Default(
                sc_signal(4))
