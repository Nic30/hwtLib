from hwt.code import power, If, Concat
from hwt.hdl.types.array import HArray
from hwt.hdl.types.arrayVal import HArrayVal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import INT, SLICE
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.integerVal import SliceVal
from hwt.interfaces.std import Signal
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class Showcase0(Unit):

    def _declr(self):
        self.a = Signal(dtype=Bits(32, signed=False))
        self.b = Signal(dtype=Bits(32, signed=True))
        self.c = Signal(dtype=Bits(32))
        self.clk = Signal(dtype=Bits(1))
        self.cmp_0 = Signal(dtype=Bits(1))
        self.cmp_1 = Signal(dtype=Bits(1))
        self.cmp_2 = Signal(dtype=Bits(1))
        self.cmp_3 = Signal(dtype=Bits(1))
        self.cmp_4 = Signal(dtype=Bits(1))
        self.cmp_5 = Signal(dtype=Bits(1))
        self.contOut = Signal(dtype=Bits(32))
        self.d = Signal(dtype=Bits(32))
        self.e = Signal(dtype=Bits(1))
        self.f = Signal(dtype=Bits(1))
        self.fitted = Signal(dtype=Bits(16))
        self.g = Signal(dtype=Bits(8))
        self.h = Signal(dtype=Bits(8))
        self.i = Signal(dtype=Bits(2))
        self.j = Signal(dtype=Bits(8))
        self.k = Signal(dtype=Bits(32))
        self.out = Signal(dtype=Bits(1))
        self.output = Signal(dtype=Bits(1))
        self.rst_n = Signal(dtype=Bits(1, negated=True))
        self.sc_signal = Signal(dtype=Bits(8))

    def _impl(self):
        a, b, c, clk, cmp_0, cmp_1, cmp_2, cmp_3, cmp_4, cmp_5, contOut, d, e, f, fitted, g, h, i, j, k, out, output, rst_n, sc_signal = self.a, self.b, self.c, self.clk, self.cmp_0, self.cmp_1, self.cmp_2, self.cmp_3, self.cmp_4, self.cmp_5, self.contOut, self.d, self.e, self.f, self.fitted, self.g, self.h, self.i, self.j, self.k, self.out, self.output, self.rst_n, self.sc_signal
        # constants 
        const_0_0 = None
        # internal signals
        const_private_signal = self._sig("const_private_signal", Bits(32, signed=False), def_val=0x7b)
        fallingEdgeRam = self._sig("fallingEdgeRam", HArray(Bits(8, signed=True), 4), def_val=None)
        r = self._sig("r", Bits(1), def_val=0x0)
        r_0 = self._sig("r_0", Bits(2), def_val=0x0)
        r_1 = self._sig("r_1", Bits(2), def_val=0x0)
        r_next = self._sig("r_next", Bits(1), def_val=None)
        r_next_0 = self._sig("r_next_0", Bits(2), def_val=None)
        r_next_1 = self._sig("r_next_1", Bits(2), def_val=None)
        rom = self._sig("rom", HArray(Bits(8, signed=False), 4), def_val={0: 0x0,
            1: 0x1,
            2: 0x2,
            3: 0x3})
        # assig_process_c sensitivity: a, b
        c((a + b._reinterpret_cast(Bits(32, signed=False)))._reinterpret_cast(Bits(32)))
        # assig_process_cmp_0 sensitivity: a
        cmp_0(a < 0x4)
        # assig_process_cmp_1 sensitivity: a
        cmp_1(a > 0x4)
        # assig_process_cmp_2 sensitivity: b
        cmp_2(b <= 0x4)
        # assig_process_cmp_3 sensitivity: b
        cmp_3(b >= 0x4)
        # assig_process_cmp_4 sensitivity: b
        cmp_4(b != 0x4)
        # assig_process_cmp_5 sensitivity: b
        cmp_5(b._eq(0x4))
        # assig_process_contOut sensitivity: 
        contOut(const_private_signal._reinterpret_cast(Bits(32)))
        # assig_process_f sensitivity: r
        f(r)
        # assig_process_fallingEdgeRam sensitivity: (SENSITIVITY.FALLING, clk)
        If(clk._onFallingEdge(),
            fallingEdgeRam[r_1]((a[8:0])._reinterpret_cast(Bits(8, signed=True))),
            k(Concat(Bits(24).from_py(0x0), ((fallingEdgeRam[r_1])._reinterpret_cast(Bits(8, signed=False)))._reinterpret_cast(Bits(8)))),
        )
        # assig_process_fitted sensitivity: a
        fitted((a[16:0])._reinterpret_cast(Bits(16)))
        # assig_process_g sensitivity: a, b
        g(Concat(Concat(a[1] & b[1], a[0] ^ b[0] | a[1]), (a[6:0])._reinterpret_cast(Bits(6))))
        # assig_process_h sensitivity: a, r
        If(a[2],
            If(r,
                h(0x0),
            ).Elif(a[1],
                h(0x1),
            ).Else(
                h(0x2),
            ),
        )
        # assig_process_j sensitivity: (SENSITIVITY.RISING, clk)
        If(clk._onRisingEdge(),
            j((rom[r_1])._reinterpret_cast(Bits(8))),
        )
        # assig_process_out sensitivity: 
        out(0x0)
        # assig_process_output sensitivity: 
        output(const_0_0)
        # assig_process_r sensitivity: (SENSITIVITY.RISING, clk)
        If(clk._onRisingEdge(),
            If(rst_n._eq(0x0),
                r_1(0x0),
                r_0(0x0),
                r(0x0),
            ).Else(
                r_1(r_next_1),
                r_0(r_next_0),
                r(r_next),
            ),
        )
        # assig_process_r_next sensitivity: i
        r_next_0(i)
        # assig_process_r_next_0 sensitivity: r_0
        r_next_1(r_0)
        # assig_process_r_next_1 sensitivity: e, r
        If(~r,
            r_next(e),
        ).Else(
            r_next(r),
        )
        # assig_process_sc_signal sensitivity: a
        If(a._eq(0x1),
            sc_signal(0x0),
        ).Elif(a._eq(0x2),
            sc_signal(0x1),
        ).Elif(a._eq(0x3),
            sc_signal(0x3),
        ).Else(
            sc_signal(0x4),
        )