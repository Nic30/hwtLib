#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch, Concat
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIORdVldSync, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtSimApi.hdlSimulator import HdlSimulator


class TwoOperandsHsAgent(HwIODataRdVldAgent):

    @override
    def get_data(self):
        i = self.hwIO
        return i.a.read(), i.b.read()

    @override
    def set_data(self, data):
        if data is None:
            a = None
            b = None
        else:
            a, b = data
        i = self.hwIO
        i.a.write(a)
        i.b.write(b)


class TwoOperandsHs(HwIODataRdVld):

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(self.DATA_WIDTH)
        self.b = HwIOVectSignal(self.DATA_WIDTH)
        HwIORdVldSync.hwDeclr(self)

    @override
    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = TwoOperandsHsAgent(sim, self)


class MultiplierBooth(HwModule):
    """
    An implementation of Booth's multiplication algorithm

    .. figure:: ./_static/MultiplierBooth_fsm.png

    :attention: The input domain is limited to range specified bellow.

    .. code-block:: python

        max = 2 ** (DATA_WIDTH - 1) - 1
        min = -1 * 2 ** (DATA_WIDTH - 1)

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self) -> None:
        self.DATA_WIDTH = HwParam(4)
        self.RESULT_WIDTH = HwParam(None)

    @override
    def hwDeclr(self):
        if self.RESULT_WIDTH is None:
            self.RESULT_WIDTH = 2 * self.DATA_WIDTH
        addClkRstn(self)
        self.dataIn = TwoOperandsHs()
        self.dataIn.DATA_WIDTH = self.DATA_WIDTH
        self.dataOut = HwIODataRdVld()._m()
        self.dataOut.DATA_WIDTH = self.RESULT_WIDTH

    @override
    def hwImpl(self) -> None:
        start = self._sig("start")
        part_res_t = HBits(self.DATA_WIDTH)
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
            HBits(log2ceil(self.DATA_WIDTH + 1), signed=False),
            def_val=0)
        done = counter._eq(0)
        waitinOnConsumer = self._reg("waitinOnConsumer", def_val=0)

        add = rename_signal(self, (a + m)._signed(), "add")
        sub = rename_signal(self, (a - m)._signed(), "sub")

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
                a(add >> 1),
                q(Concat(add[0], q[:1])),
            ).Case(0b10,
                # substract multiplicand from left half of product
                a(sub >> 1),
                q(Concat(sub[0], q[:1])),
            ).Default(
                a(a._signed() >> 1),
                q(Concat(a[0], q[:1])),
            ),
            q_1(q[0]),
            counter(counter - 1)
        )

        If(start,
            waitinOnConsumer(1)
        ).Elif(done & dout.rd,
            waitinOnConsumer(0),
        )

        dout.data(Concat(a, q)._vec())
        dout.vld(done & waitinOnConsumer)
        start(din.vld & done & ~waitinOnConsumer)
        din.rd(done & ~waitinOnConsumer)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = MultiplierBooth()
    print(to_rtl_str(m))

