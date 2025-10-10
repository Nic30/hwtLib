#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import Concat, If, Switch
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal, HwIOBramPort_noClk
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.types.net.arp import arp_ipv4_t


class SimpleConcat(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a0 = HwIOSignal()
        self.a1 = HwIOSignal()
        self.a2 = HwIOSignal()
        self.a3 = HwIOSignal()

        self.a_out = HwIOVectSignal(4)._m()

    @override
    def hwImpl(self):
        self.a_out(Concat(self.a3, self.a2, self.a1, self.a0))


class ConcatAssign(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a0 = HwIOSignal()._m()
        self.a1 = HwIOSignal()._m()
        self.a2 = HwIOSignal()._m()
        self.a3 = HwIOSignal()._m()

        self.a_in = HwIOVectSignal(4)

    @override
    def hwImpl(self):
        # verilog like {a3, a2, a1, a0} = a_in
        Concat(self.a3, self.a2, self.a1, self.a0)(self.a_in)


class ConcatIndexAssignMix0(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a = HwIOArray([HwIOVectSignal(2), HwIOVectSignal(2)])
        self.b = HwIOArray(HwIOSignal() for _ in range(4))._m()

    @override
    def hwImpl(self) -> None:
        a = Concat(*reversed(self.a))
        for i, b in enumerate(self.b):
            b(a[i])


class ConcatIndexAssignMix1(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a = HwIOArray(HwIOSignal() for _ in range(4))
        self.b = HwIOArray([HwIOVectSignal(2), HwIOVectSignal(2)])._m()

    @override
    def hwImpl(self) -> None:
        b = Concat(*reversed(self.b))
        for i, a in enumerate(self.a):
            b[i](a)


class ConcatIndexAssignMix2(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a = HwIOArray([HwIOVectSignal(2), HwIOVectSignal(4), HwIOVectSignal(2)])
        self.b = HwIOArray([HwIOVectSignal(4), HwIOVectSignal(4)])._m()

    @override
    def hwImpl(self) -> None:
        b = Concat(*reversed(self.b))
        a0, a1, a2 = self.a
        b[:6](a2)
        b[6:2](a1)
        b[2:](a0)


class ConcatIndexAssignMix3(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.port = HwIOBramPort_noClk()
        self.port.DATA_WIDTH = 24

    @override
    def hwImpl(self) -> None:
        port = self.port
        d = self._reg("d", arp_ipv4_t, def_val={f.name: i for i, f in enumerate(arp_ipv4_t.fields)})
        d_flat = d._reinterpret_cast(HBits(d._dtype.bit_length()))
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
                out_src = Concat(HBits(end - d_w).from_py(0), d_flat[d_w:start])
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
    from hwt.synth import to_rtl_str

    m = ConcatIndexAssignMix3()
    print(to_rtl_str(m))
