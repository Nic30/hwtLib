#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import Concat, If, Switch
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal, BramPort_withoutClk
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.unit import Unit
from hwtLib.types.net.arp import arp_ipv4_t


class SimpleConcat(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a0 = Signal()
        self.a1 = Signal()
        self.a2 = Signal()
        self.a3 = Signal()

        self.a_out = VectSignal(4)._m()

    def _impl(self):
        self.a_out(Concat(self.a3, self.a2, self.a1, self.a0))


class ConcatAssign(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a0 = Signal()._m()
        self.a1 = Signal()._m()
        self.a2 = Signal()._m()
        self.a3 = Signal()._m()

        self.a_in = VectSignal(4)

    def _impl(self):
        # verilog like {a3, a2, a1, a0} = a_in
        Concat(self.a3, self.a2, self.a1, self.a0)(self.a_in)


class ConcatIndexAssignMix0(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = HObjList([VectSignal(2), VectSignal(2)])
        self.b = HObjList([Signal()._m() for _ in range(4)])

    def _impl(self) -> None:
        a = Concat(*reversed(self.a))
        for i, b in enumerate(self.b):
            b(a[i])


class ConcatIndexAssignMix1(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = HObjList([Signal() for _ in range(4)])
        self.b = HObjList([VectSignal(2)._m(), VectSignal(2)._m()])

    def _impl(self) -> None:
        b = Concat(*reversed(self.b))
        for i, a in enumerate(self.a):
            b[i](a)


class ConcatIndexAssignMix2(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = HObjList([VectSignal(2), VectSignal(4), VectSignal(2)])
        self.b = HObjList([VectSignal(4)._m(), VectSignal(4)._m()])

    def _impl(self) -> None:
        b = Concat(*reversed(self.b))
        a0, a1, a2 = self.a
        b[:6](a2)
        b[6:2](a1)
        b[2:](a0)


class ConcatIndexAssignMix3(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        addClkRstn(self)
        self.port = BramPort_withoutClk()
        self.port.DATA_WIDTH = 24

    def _impl(self) -> None:
        port = self.port
        d = self._reg("d", arp_ipv4_t, def_val={f.name: i for i, f in enumerate(arp_ipv4_t.fields)})
        d_flat = d._reinterpret_cast(Bits(d._dtype.bit_length()))
        rd_cases = []
        wr_cases = []
        d_w = d_flat._dtype.bit_length()
        for i in range(ceil(d_w / 24)):
            start = i * 24
            end = (i + 1) * 24
            if end <= d_w:
                out_src = d_flat[end:start]
                in_dst_assig = out_src(port.din)
            else:
                out_src = Concat(Bits(end - d_w).from_py(0), d_flat[d_w:start])
                in_dst_assig = d_flat[d_w:start](port.din[d_w - start:])

            rd_cases.append((i, port.dout(out_src)))
            wr_cases.append((i, in_dst_assig))

        If(self.clk._onRisingEdge() & port.en,
           Switch(port.addr)\
            .add_cases(rd_cases)\
            .Default(port.dout(None)),
        )
        If(port.en & port.we,
            Switch(port.addr)\
             .add_cases(wr_cases)
        )


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = ConcatIndexAssignMix3()
    print(to_rtl_str(u))
