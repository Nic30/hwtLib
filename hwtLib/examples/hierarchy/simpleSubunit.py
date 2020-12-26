#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit
from hwtLib.examples.simple import SimpleUnit


class SimpleSubunit(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.a = Signal()
        self.b = Signal()._m()

        # Here we instantiate our subunit and register it by assigning
        # to property of self it can be done in _impl as well,
        # but if you do it here, it offers more possibilities for parallelization
        self.subunit0 = SimpleUnit()

    def _impl(self):
        u = self.subunit0
        u.a(self.a)
        self.b(u.b)
        # Any configuration for subcomponents in _impl has to be done before registering
        # The subcomponent has to be always registered on parent :class:`hwt.synthesizer.unit.Unit` otherwise
        # it won't be discovered and initialized.


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = SimpleSubunit()
    from hwt.serializer.vhdl import Vhdl2008Serializer

    print(to_rtl_str(u, serializer_cls=Vhdl2008Serializer))
