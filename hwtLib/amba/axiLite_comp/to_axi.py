#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axi4 import Axi4, Axi4_addr
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.constants import BURST_INCR, CACHE_DEFAULT, LOCK_DEFAULT, \
    BYTES_IN_TRANS, QOS_DEFAULT


def interface_not_present_on_other(a: Interface, b: Interface):
    """
    :return: set of interfaces which does not have an equivalent on "b"
    """
    missing_on_b = []
    for a in a._interfaces:
        on_b = getattr(b, a._name, None)
        if on_b is None:
            missing_on_b.append(a)

    return set(missing_on_b)


@serializeParamsUniq
class AxiLite_to_Axi(BusBridge):
    """
    Bridge from AxiLite interface to Axi3/4 interface

    .. hwt-autodoc::
    """

    def __init__(self, intfCls=Axi4, hdl_name_override:Optional[str]=None):
        self.intfCls = intfCls
        super(AxiLite_to_Axi, self).__init__(hdl_name_override=hdl_name_override)

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.intfCls._config(self)
        self.DEFAULT_ID = Param(0)

    def _declr(self):
        with self._paramsShared():
            self.s = Axi4Lite()
            self.m = self.intfCls()._m()

    def _impl(self) -> None:
        axiFull = self.m
        axiLite = self.s

        def connect_what_is_same_lite_to_full(src, dst):
            dst(src, exclude=interface_not_present_on_other(dst, src))

        def connect_what_is_same_full_to_lite(src, dst):
            dst(src, exclude=interface_not_present_on_other(src, dst))

        def a_defaults(a: Axi4_addr):
            a.id(self.DEFAULT_ID)
            a.burst(BURST_INCR)
            a.cache(CACHE_DEFAULT)
            a.len(0)
            a.lock(LOCK_DEFAULT)
            a.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))
            if hasattr(a, "qos"):
                # axi3/4 difference
                a.qos(QOS_DEFAULT)

        connect_what_is_same_lite_to_full(axiLite.ar, axiFull.ar)
        a_defaults(axiFull.ar)
        connect_what_is_same_lite_to_full(axiLite.aw, axiFull.aw)
        a_defaults(axiFull.aw)
        connect_what_is_same_lite_to_full(axiLite.w, axiFull.w)
        if hasattr(axiFull.w, "id"):
            # axi3/4 difference
            axiFull.w.id(self.DEFAULT_ID)
        axiFull.w.last(1)
        connect_what_is_same_full_to_lite(axiFull.r, axiLite.r)
        connect_what_is_same_full_to_lite(axiFull.b, axiLite.b)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = AxiLite_to_Axi()
    print(to_rtl_str(u))
