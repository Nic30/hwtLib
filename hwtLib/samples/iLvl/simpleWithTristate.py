#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import Unit
from hwt.interfaces.tristate import TristateSig


class SimpleUnit(Unit):
    def _declr(self):
        self.a = TristateSig()
        self.b = TristateSig()

    def _impl(self):
        self.b ** self.a 

if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.shortcuts import toRtl
    u = SimpleUnit()
    print(toRtl(u))
