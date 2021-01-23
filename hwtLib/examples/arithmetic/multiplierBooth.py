#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch, Concat
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked, HandshakeSync, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from hwt.synthesizer.vectorUtils import fitTo
from hwt.code_utils import rename_signal


class TwoOperandsHsAgent(HandshakedAgent):

    def get_data(self):
        i = self.intf
        return i.a.read(), i.b.read()

    def set_data(self, data):
        if data is None:
            a = None
            b = None
        else:
            a, b = data
        i = self.intf
        i.a.write(a)
        i.b.write(b)


class TwoOperandsHs(Handshaked):

    def _declr(self):
        self.a = VectSignal(self.DATA_WIDTH)
        self.b = VectSignal(self.DATA_WIDTH)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = TwoOperandsHsAgent(sim, self)


class MultiplerBooth(Unit):
    """
    An implementation of Booth's multiplication algorithm

    .. figure:: ./_static/MultiplerBooth_fsm.png

    :attention: The input domain is limited to range specified bellow.

    .. code-block:: python

        max = 2 ** (DATA_WIDTH - 1) - 1
        min = -1 * 2 ** (DATA_WIDTH - 1)

    .. hwt-autodoc::
    """

    def _config(self) -> None:
        self.DATA_WIDTH = Param(4)
        self.RESULT_WIDTH = Param(None)

    def _declr(self):
        if self.RESULT_WIDTH is None:
            self.RESULT_WIDTH = 2 * self.DATA_WIDTH
        addClkRstn(self)
        self.dataIn = TwoOperandsHs()
        self.dataIn.DATA_WIDTH = self.DATA_WIDTH
        self.dataOut = Handshaked()._m()
        self.dataOut.DATA_WIDTH = self.RESULT_WIDTH

    def _impl(self) -> None:
        start = self._sig("start")
        part_res_t = Bits(self.DATA_WIDTH)
        # High-order n bits of product
        a = self._reg("a", part_res_t)
        # multiplicand
        m = self._reg("m", part_res_t)
        # Initially holds multiplier, ultimately holds low-order n bits of product
        q = self._reg("q", part_res_t)
        # previous bit 0 of q
        q_1 = self._reg("q_1")

        din = self.dataIn
        dout = self.dataOut

        counter = self._reg(
            "counter",
            Bits(log2ceil(self.RESULT_WIDTH + 1), signed=False),
            def_val=0)
        done = counter._eq(0)
        waitinOnConsummer = self._reg("waitinOnConsummer", def_val=0)

        # we need 1 bit more for the overflow
        #t = Bits(self.DATA_WIDTH + 1, signed=False)
        #_a = a._reinterpret_cast(t)
        #_m = m._reinterpret_cast(t)
        #add = rename_signal(self, _a + _m, "add")
        #sub = rename_signal(self, _a - _m, "sub")

        add = rename_signal(self, (a + m)._signed(), "add")
        sub = rename_signal(self, (a - m)._signed(), "sub")

        #sub = rename_signal(self, (a + ~m + 1)._signed(), "sub")
        #sub_tmp = rename_signal(self, a - m, "sub_tmp")
        #sub = rename_signal(self, sub_tmp._signed(), "sub")
        #sub_shifted = rename_signal(self, sub >> 1, "sub_shifted")
        #print(sub_shifted.drivers)
        If(start,
            a(0),
            m(din.a),
            q(din.b),
            q_1(0),
            counter(self.DATA_WIDTH),
        ).Elif(~done,
            Switch(Concat(q[0], q_1))
            .Case(0b01,
                # add multiplicand to left half of product
                #a(add[:1]),
                a(add >> 1),
                q(Concat(add[0], q[:1])),
            ).Case(0b10,
                # substract multiplicand from left half of product
                #a(sub[:1]),
                a(sub >> 1),
                q(Concat(sub[0], q[:1])),
            ).Default(
                a(a._signed() >> 1),
                q(Concat(a[0], q[:1])),
            ),
            q_1(q[0]),
            counter(counter - 1)
        )
        #print(x)
        If(start,
            waitinOnConsummer(1)
        ).Elif(done & dout.rd,
            waitinOnConsummer(0),
        )

        dout.data(Concat(a, q)._vec())
        dout.vld(done & waitinOnConsummer)
        start(din.vld & done & ~waitinOnConsummer)
        din.rd(done & ~waitinOnConsummer)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = MultiplerBooth()
    print(to_rtl_str(u))