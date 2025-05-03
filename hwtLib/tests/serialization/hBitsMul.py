#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwModule import HwModule


class ExampleHBitsMul0a(HwModule):

    def hwDeclr(self) -> None:
        self.a = HwIOVectSignal(16)
        self.b = HwIOVectSignal(16)
        self.res = HwIOVectSignal(16)._m()

    def hwImpl(self) -> None:
        # in VHDL result of multiplication is 2x the width, during serialization there must be tmp variable to slice off top bits
        self.res(self.a * self.b)


class ExampleHBitsMul0b(HwModule):

    def hwDeclr(self) -> None:
        self.a = HwIOVectSignal(16)
        self.b = HwIOVectSignal(16)
        self.c = HwIOVectSignal(16)
        self.res = HwIOVectSignal(16)._m()

    def hwImpl(self) -> None:
        # in VHDL result of multiplication is 2x the width, during serialization there must be tmp variable to slice off top bits
        self.res(self.a * self.b + self.c)


class ExampleHBitsMul1a(HwModule):

    def hwDeclr(self) -> None:
        self.a = HwIOVectSignal(8)
        self.b = HwIOVectSignal(8)
        self.res = HwIOVectSignal(16)._m()

    def hwImpl(self) -> None:
        # in VHLD this should be recognized during serialization and there should not be any cast
        self.res(self.a._zext(16) * self.b._zext(16))


class ExampleHBitsMulS1a(HwModule):

    def hwDeclr(self) -> None:
        self.a = HwIOVectSignal(8)
        self.b = HwIOVectSignal(8)
        self.res = HwIOVectSignal(16)._m()

    def hwImpl(self) -> None:
        # in VHLD this should be recognized during serialization and there should not be any cast
        self.res(self.a._sext(16) * self.b._sext(16))


class ExampleHBitsMul1b(HwModule):

    def hwDeclr(self) -> None:
        self.a = HwIOVectSignal(8)
        self.b = HwIOVectSignal(8)
        self.c = HwIOVectSignal(16)
        self.res = HwIOVectSignal(16)._m()

    def hwImpl(self) -> None:
        # in VHLD this should be recognized during serialization and there should not be any cast
        self.res(self.a._zext(16) * self.b._zext(16) + self.c)


class ExampleHBitsMul1c(HwModule):

    def hwDeclr(self) -> None:
        self.a = HwIOVectSignal(8, signed=True)
        self.b = HwIOVectSignal(8, signed=True)
        self.c = HwIOVectSignal(16, signed=True)
        self.res = HwIOVectSignal(16, signed=True)._m()

    def hwImpl(self) -> None:
        # in VHLD this should be recognized during serialization and there should not be any cast
        self.res(self.a._zext(16) * self.b._zext(16) + self.c)


class ExampleHBitsMulS1b(HwModule):

    def hwDeclr(self) -> None:
        ExampleHBitsMul1b.hwDeclr(self)

    def hwImpl(self) -> None:
        # in VHLD this should be recognized during serialization and there should not be any cast
        self.res(self.a._sext(16) * self.b._sext(16) + self.c)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = ExampleHBitsMul1c()
    print(to_rtl_str(m))
