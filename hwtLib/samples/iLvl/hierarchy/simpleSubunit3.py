#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import Unit, Param
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.iLvl.simpleAxiStream import SimpleUnitAxiStream


class SimpleSubunit3(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(128)
        
    def _declr(self):
        with self._paramsShared():
            self.subunit0 = SimpleUnitAxiStream() 
            
            self.a0 = AxiStream()
            self.b0 = AxiStream()
        
    def _impl(self):
        u = self.subunit0
        u.a ** self.a0
        self.b0 ** u.b

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleSubunit3))
