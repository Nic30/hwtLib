#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import s
from hwt.serializer.constants import SERI_MODE
from hwt.code import log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam


class BinToOneHot(Unit):
    _serializerMode = SERI_MODE.PARAMS_UNIQ
    
    def _config(self):
        self.DATA_WIDTH = Param(32)
    
    def _declr(self):
        self.din = s(dtype=vecT(log2ceil(self.DATA_WIDTH)))
        self.en = s()
        self.dout = s(dtype=vecT(self.DATA_WIDTH))

    def _impl(self):
        en = self.en
        dIn = self.din
        
        WIDTH = self.DATA_WIDTH
        # empty_gen
        if evalParam(WIDTH).val == 1:
            self.dout[0] ** en
        else:
            # full_gen
            for i in range(evalParam(WIDTH).val):
                self.dout[i] ** (dIn._eq(i) & en)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(BinToOneHot))
