#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthesizer.codeOps import Concat
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit


class SimpleConcat(Unit):
    def _declr(self):
        with self._asExtern():
            self.a0 = Signal()
            self.a1 = Signal()
            self.a2 = Signal()
            self.a3 = Signal()
    
            self.a_out = Signal(dtype=vecT(4))
    
    def _impl(self):
        self.a_out ** Concat(self.a3, self.a2, self.a1, self.a0)
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleConcat))
