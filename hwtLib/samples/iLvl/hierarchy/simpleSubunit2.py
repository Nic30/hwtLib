#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.iLvl.simpleAxiStream import SimpleUnitAxiStream


class SimpleSubunit2(Unit):
    def _declr(self):
        self.subunit0 = SimpleUnitAxiStream()
        self.a0 = AxiStream()
        self.b0 = AxiStream()
            
        self.a0.DATA_WIDTH.set(8)
        self.b0.DATA_WIDTH.set(8)
    
    def _impl(self):
        u = self.subunit0
        u.a ** self.a0
        self.b0 ** u.b

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleSubunit2))
