#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit


class SimpleComentedUnit(Unit):
    """
    This is comment for SimpleComentedUnit entity, it will be rendered before entity as comment.
    Do not forget that class inheritance does apply for docstring as well.
    """

    def _declr(self):
        self.a = Signal()
        self.b = Signal()._m()

    def _impl(self):
        self.b(self.a)


class SimpleComentedUnit2(SimpleComentedUnit):
    """single line"""
    pass


class SimpleComentedUnit3(SimpleComentedUnit2):
    pass


SimpleComentedUnit3.__doc__ = "dynamically generated, for example loaded from file or builded from unit content"


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(SimpleComentedUnit))
    print(to_rtl_str(SimpleComentedUnit2))
    print(to_rtl_str(SimpleComentedUnit3))
