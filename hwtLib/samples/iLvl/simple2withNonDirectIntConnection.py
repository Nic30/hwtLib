#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.intfLvl import Param, connect, Unit
from hwtLib.interfaces.amba import AxiStream


class Simple2withNonDirectIntConnection(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        with self._paramsShared():
            with self._asExtern():
                self.a = AxiStream()
                self.c = AxiStream()
            self.b = AxiStream()
        
    def _impl(self):
        b = self.b
        connect(self.a, b)
        connect(b, self.c)
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(Simple2withNonDirectIntConnection))
