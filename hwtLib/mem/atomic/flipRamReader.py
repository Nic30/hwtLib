#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import BramPort_withoutClk
from hwtLib.handshaked.ramReader import HsRamPortReader


class HsFlipRamReader(HsRamPortReader):
    """
    Same as HsBramPortReader but has one BRAM port more.
    Every data which is readed, is  overwritten with 0.
    """
    def _declr(self):
        super()._declr()
        with self._paramsShared():
            self.dataWriteBack = BramPort_withoutClk()
                
    
    def cleanAfterRead(self):
        st = self.st
        st_t = st._dtype
        wb = self.dataWriteBack
        wb.we ** (self.data_flag & st._eq(st_t.sendingData))
        wb.din ** 0
        wb.en ** 1
        wb.addr ** self.addr 
                
    def _impl(self):
        HsRamPortReader._impl(self)
        self.cleanAfterRead()
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = HsFlipRamReader()
    print(toRtl(u))        
