#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import Param, Unit
from hwtLib.amba.axis import AxiStream


class Simple2withNonDirectIntConnection(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        with self._paramsShared():
            self.a = AxiStream()
            self.c = AxiStream()
        
    def _impl(self):
        # we have to register interface on this unit first before use
        with self._paramsShared():
            self.b = AxiStream()
        b = self.b 

        b ** self.a
        self.c ** b
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(Simple2withNonDirectIntConnection))
