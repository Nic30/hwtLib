#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.hwParam import HwParam
from hwtLib.abstract.busStaticRemap import BusStaticRemap
from hwtLib.amba.axi4 import Axi4


class Axi4StaticRemap(BusStaticRemap):
    """
    :class:`.BusStaticRemap` implementation for AXI3/4 full/lite interfaces
    :note: this component only remaps some memory regions, but it does not perform the address checking

    .. hwt-autodoc:: _example_Axi4StaticRemap
    """

    def __init__(self, hwIOCls=Axi4, hdlName:Optional[str]=None):
        self.hwIOCls = hwIOCls
        super(Axi4StaticRemap, self).__init__(hdlName=hdlName)

    def hwConfig(self):
        self.HWIO_CLS = HwParam(self.hwIOCls)
        BusStaticRemap.hwConfig(self)
        self.hwIOCls.hwConfig(self)

    def hwImpl(self):
        # for each remaped region substitute the address offset
        self.m(self.s, exclude={self.s.ar.addr, self.s.aw.addr})
        MM = self.MEM_MAP
        self.translate_addr_signal(
            MM, self.s.ar.addr, self.m.ar.addr)
        self.translate_addr_signal(
            MM, self.s.aw.addr, self.m.aw.addr)


def _example_Axi4StaticRemap():
    m = Axi4StaticRemap()
    m.MEM_MAP = [(0x0, 0x1000, 0x1000),
                 (0x1000, 0x1000, 0x0),
                 ]
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_Axi4StaticRemap()
    print(to_rtl_str(m))
