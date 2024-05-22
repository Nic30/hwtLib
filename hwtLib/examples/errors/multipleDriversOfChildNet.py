#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class ExampleChild(HwModule):
    @override
    def hwDeclr(self):
        self.c = HwIODataRdVld()
        self.d = HwIODataRdVld()._m()

    @override
    def hwImpl(self):
        self.d(self.c)


class MultipleDriversOfChildNet(HwModule):
    @override
    def hwDeclr(self):
        self.a = HwIODataRdVld()
        self.b = HwIODataRdVld()._m()

        self.ch = ExampleChild()

    @override
    def hwImpl(self):
        # interface directions in collision
        self.ch.d(self.a)
        self.ch.c.data(1)
        self.ch.c.vld(1)
        self.b(self.ch.c)


class MultipleDriversOfChildNet2(MultipleDriversOfChildNet):
    @override
    def hwImpl(self):
        self.ch.c(self.a)
        self.b(self.ch.d)
        # another colliding driver for b.vld
        self.b.vld(1)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = MultipleDriversOfChildNet()
    # hwt.serializer.exceptions.SerializerException
    print(to_rtl_str(m))
