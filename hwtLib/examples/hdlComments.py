#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class SimpleComentedHwModule(HwModule):
    """
    This is comment for SimpleComentedHwModule entity, it will be rendered before entity as comment.
    Do not forget that class inheritance does apply for docstring as well.
    """

    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class SimpleComentedHwModule2(SimpleComentedHwModule):
    """single line"""
    pass


class SimpleComentedHwModule3(SimpleComentedHwModule2):
    pass


SimpleComentedHwModule3.__doc__ = "dynamically generated, for example loaded from file or builded from unit content"


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(SimpleComentedHwModule))
    print(to_rtl_str(SimpleComentedHwModule2))
    print(to_rtl_str(SimpleComentedHwModule3))
