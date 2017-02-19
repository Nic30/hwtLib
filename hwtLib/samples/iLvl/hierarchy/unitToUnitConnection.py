#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import Param, Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.iLvl.simple2withNonDirectIntConnection import Simple2withNonDirectIntConnection


class UnitToUnitConnection(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        with self._paramsShared():
            self.a = AxiStream()
            self.b = AxiStream()
    
            self.u0 = Simple2withNonDirectIntConnection()
            self.u1 = Simple2withNonDirectIntConnection()
        
    def _impl(self):
        self.u0.a ** self.a
        self.u1.a ** self.u0.c
        self.b ** self.u1.c 
    
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(UnitToUnitConnection))
