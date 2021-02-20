#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import VectSignal, Signal, HandshakeSync
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.cesnet.mi32.intf import Mi32


class Mi32AddrHs(HandshakeSync):
    """
    Equivalent of Mi32 address/write data channel
    with HandshakeSync compatible signal names

    .. hwt-autodoc::
    """
    def _config(self):
        Mi32._config(self)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.read = Signal()
        self.write = Signal()
        self.be = VectSignal(self.DATA_WIDTH // 8)
        self.dwr = VectSignal(self.DATA_WIDTH)
        super(Mi32AddrHs, self)._declr()


class Mi32Buff(BusBridge):
    """
    Buffer for Mi32 interface

    .. hwt-autodoc::
    """

    def _config(self):
        Mi32._config(self)
        self.ADDR_BUFF_DEPTH = Param(1)
        self.DATA_BUFF_DEPTH = Param(1)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.s = Mi32()
            self.m = Mi32()._m()

    def _Mi32_addr_to_Mi32AddrHs(self, mi32: Mi32, tmp_name):
        tmp = Mi32AddrHs()
        tmp._updateParamsFrom(mi32)
        setattr(self, tmp_name, tmp)
        tmp(mi32, exclude={
            tmp.vld, tmp.rd, tmp.read, tmp.write,
            mi32.ardy, mi32.rd, mi32.wr, mi32.drd, mi32.drdy})
        tmp.read(mi32.rd)
        tmp.write(mi32.wr)
        tmp.vld(mi32.rd | mi32.wr)
        mi32.ardy(tmp.rd)
        return tmp

    def _connect_Mi32AddrHs_to_Mi32(self, mi32ahs: Mi32AddrHs, mi32: Mi32):
        return [
            mi32(mi32ahs, exclude={
                mi32ahs.vld, mi32ahs.rd, mi32ahs.read, mi32ahs.write,
                mi32.ardy, mi32.rd, mi32.wr, mi32.drd, mi32.drdy}),
            mi32.rd(mi32ahs.vld & mi32ahs.read),
            mi32.wr(mi32ahs.vld & mi32ahs.write),
            mi32ahs.rd(mi32.ardy),
        ]

    def _impl(self):
        m = self._Mi32_addr_to_Mi32AddrHs(self.s, "addr_tmp")
        m = HsBuilder(self, m).buff(items=self.ADDR_BUFF_DEPTH).end
        self._connect_Mi32AddrHs_to_Mi32(m, self.m)

        data_t = HStruct(
            (self.m.drd._dtype, "drd"),  # read data
            (BIT, "drdy"),  # read data valid
        )
        m = (self.m.drd, self.m.drdy)

        for i in range(self.DATA_BUFF_DEPTH):
            reg = self._reg(f"read_data_reg{i:d}", data_t, def_val={"drdy": 0})
            reg.drd(m[0])
            reg.drdy(m[1])
            m = (reg.drd, reg.drdy)

        self.s.drd(m[0])
        self.s.drdy(m[1])


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str

    u = Mi32Buff()
    print(to_rtl_str(u))
