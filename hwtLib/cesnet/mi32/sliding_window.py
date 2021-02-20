#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.utils import addClkRstn
from hwt.math import isPow2
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.cesnet.mi32.intf import Mi32


class Mi32SlidingWindow(BusBridge):
    """
    Address space window + offset register which allows to address bigger
    address space than available on input interface due size of its address signal

    :note: address_space = HStruct(
        (Bits(8)[WINDOW_SIZE], "window"),
        (Bits(DATA_WIDTH),     "offset"),
        )
    :note: offset is write only
    :ivar ~.WINDOW_SIZE: size of window to "m" interface
        also the address of offset register

    .. hwt-autodoc::
    """

    def _config(self):
        Mi32._config(self)
        self.M_ADDR_WIDTH = Param(self.ADDR_WIDTH + 1)
        self.WINDOW_SIZE = Param(4096)

    def _declr(self):
        assert isPow2(self.WINDOW_SIZE), self.WINDOW_SIZE
        assert self.M_ADDR_WIDTH > self.ADDR_WIDTH, (self.M_ADDR_WIDTH, self.ADDR_WIDTH)
        assert (2 ** self.M_ADDR_WIDTH) >= self.WINDOW_SIZE, (
            "has to be large enough in order to address whole window",
            self.M_ADDR_WIDTH, self.WINDOW_SIZE
        )
        addClkRstn(self)
        with self._paramsShared(exclude=({"ADDR_WIDTH"}, {})):
            self.m = Mi32()._m()
            self.m.ADDR_WIDTH = self.M_ADDR_WIDTH
            self.s = Mi32()
            self.s.ADDR_WIDTH = self.ADDR_WIDTH

    def _impl(self):
        OFFSET_REG_ADDR = self.WINDOW_SIZE

        s, m = self.s, self.m
        offset_en = s.addr._eq(OFFSET_REG_ADDR)
        offset = self._reg("offset", m.addr._dtype, def_val=0)
        m(s, exclude={m.addr, m.wr, m.ardy})
        m.addr(offset + s.addr._reinterpret_cast(m.addr._dtype))
        m.wr(s.wr & ~offset_en)
        If(offset_en & s.wr,
           offset(s.dwr, fit=True)
        )
        s.ardy(m.ardy | (s.wr & offset_en))


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str

    u = Mi32SlidingWindow()
    u.ADDR_WIDTH = 16
    u.M_ADDR_WIDTH = 32
    print(to_rtl_str(u))
