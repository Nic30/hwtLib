#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwModule import HwModule
from hwtLib.amba.axi4s import Axi4Stream


class InconsistentIntfDirection(HwModule):
    def _declr(self):
        self.a = Axi4Stream()._m()

    def _impl(self):
        # missing drivers of self.a
        pass


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = InconsistentIntfDirection()
    # expecting hwt.synthesizer.exceptions.IntfLvlConfErr
    print(to_rtl_str(m))
