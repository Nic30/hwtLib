#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.synthesizer.param import Param
from hwtLib.abstract.busStaticRemap import BusStaticRemap
from hwtLib.amba.axi4 import Axi4


class AxiStaticRemap(BusStaticRemap):
    """
    :class:`.BusStaticRemap` implementation for AXI3/4 full/lite interfaces
    :note: this component only remaps some memory regions, but it does not perform the address checking

    .. hwt-autodoc:: _example_AxiStaticRemap
    """

    def __init__(self, intfCls=Axi4, hdl_name_override:Optional[str]=None):
        self.intfCls = intfCls
        super(AxiStaticRemap, self).__init__(hdl_name_override=hdl_name_override)

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        BusStaticRemap._config(self)
        self.intfCls._config(self)

    def _impl(self):
        # for each remaped region substitute the address offset
        self.m(self.s, exclude={self.s.ar.addr, self.s.aw.addr})
        MM = self.MEM_MAP
        self.translate_addr_signal(
            MM, self.s.ar.addr, self.m.ar.addr)
        self.translate_addr_signal(
            MM, self.s.aw.addr, self.m.aw.addr)


def _example_AxiStaticRemap():
    u = AxiStaticRemap()
    u.MEM_MAP = [(0x0, 0x1000, 0x1000),
                 (0x1000, 0x1000, 0x0),
                 ]
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiStaticRemap()
    print(to_rtl_str(u))
