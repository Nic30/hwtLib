#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwtLib.examples.simpleHwModule import SimpleHwModule


class SimpleSubHwModule1(HwModule):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()._m()

        # Here we instantiate our subunit and register it by assigning
        # to property of self it can be done in _impl as well,
        # but if you do it here, it offers more possibilities for parallelization
        self.submodule0 = SimpleHwModule()

    def _impl(self):
        m = self.submodule0
        m.a(self.a)
        self.b(m.b)
        # Any configuration for subcomponents in _impl has to be done before registering
        # The subcomponent has to be always registered on parent :class:`hwt.hwModule.HwModule` otherwise
        # it won't be discovered and initialized.


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    from hwt.serializer.vhdl import Vhdl2008Serializer
    
    m = SimpleSubHwModule1()
    print(to_rtl_str(m, serializer_cls=Vhdl2008Serializer))
