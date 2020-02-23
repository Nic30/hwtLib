#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, connect, Switch, If, Or, SwitchLogic
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.abstract.busInterconnect import BusInterconnect, AUTO_ADDR
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.mi32.intf import Mi32
from pyMathBitPrecise.bit_utils import selectBitRange


class Mi32InterconnectMatrix(BusInterconnect):
    """
    Simple matrix interconnect for Mi32 interface

    .. hwt-schematic:: _example_Mi32InterconnectMatrix
    """

    def _config(self) -> None:
        super(Mi32InterconnectMatrix, self)._config()
        Mi32._config(self)
        self.MAX_TRANS_OVERLAP = Param(4)

    def _declr(self) -> None:
        self._normalize_config()
        addClkRstn(self)

        slavePorts = HObjList()
        for _ in self.MASTERS:
            s = Mi32()
            s._updateParamsFrom(self)
            slavePorts.append(s)

        self.s = slavePorts

        masterPorts = HObjList()
        for _, size in self.SLAVES:
            m = Mi32()._m()
            m.ADDR_WIDTH = log2ceil(size - 1)
            m.DATA_WIDTH = self.DATA_WIDTH
            masterPorts.append(m)

        self.m = masterPorts

        # fifo which keeps index of slave for master read transaction
        # so the interconnect can delivery the readed data to master
        # which asked for it
        f = self.r_data_order = HandshakedFifo(Handshaked)
        f.DEPTH = self.MAX_TRANS_OVERLAP
        f.DATA_WIDTH = log2ceil(len(self.SLAVES))

    def _impl(self) -> None:
        if len(self.MASTERS) > 1:
            raise NotImplementedError()
        propagateClkRstn(self)
        m = self.s[0]

        r_order = self.r_data_order.dataIn
        AW = int(self.ADDR_WIDTH)
        rdata = []
        r_data_t = HStruct(
            (m.drd._dtype, "data"),
            (BIT, "vld"),
        )
        for i, (s, (s_offset, s_size)) in\
                enumerate(zip(self.m, self.SLAVES)):
            # s = Mi32()
            connect(m.addr, s.addr, fit=True)
            s.be(m.be)

            s.dwr(m.dwr)

            bitsOfSubAddr = log2ceil(s_size - 1)
            prefix = selectBitRange(
                s_offset, bitsOfSubAddr, AW - bitsOfSubAddr)
            cs = self._sig("m_cs_%d" % i)
            cs(m.addr[AW:bitsOfSubAddr]._eq(prefix))
            s.rd(m.rd & cs & r_order.rd)
            s.wr(m.wr & cs & r_order.rd)

            # we have to add 1 read data latency because the slave index would not be ready
            # oder fifo
            r_data_tmp = self._reg("r_data%d_tmp" % i, r_data_t,
                                   def_val={"vld": 0})
            r_data_tmp.data(s.drd)
            r_data_tmp.vld(s.drdy)
            rdata.append((i, cs & s.ardy, r_data_tmp))

        # r_data_order feed
        SwitchLogic(
            [(addr_en, r_order.data(i)) for i, addr_en, _ in rdata],
            default=r_order.data(None)
        )
        addr_ack = Or(*[x[1] for x in rdata])
        r_order.vld(addr_ack & m.rd)
        # m = Mi32()
        m.ardy(addr_ack & r_order.rd & (m.rd | m.wr))

        r_order = self.r_data_order.dataOut
        If(r_order.vld,
            Switch(r_order.data).addCases(
                [(slave_i, m.drd(data.data)) for slave_i, _, data in rdata],
            ).Default(
                # this case can not happen unless bug in code
                m.drd(None),
                m.drdy(None)
            )
        ).Else(
            m.drd(None),
            m.drdy(False),
        )
        r_order.rd(Or(*[data.vld for _, _, data in rdata]))


def _example_Mi32InterconnectMatrix():
    AUTO = AUTO_ADDR
    u = Mi32InterconnectMatrix()
    u.MASTERS = (({0, 1, 2, 3}), )
    u.SLAVES = (
        (0x0000, 0x100),
        (0x0100, 0x100),
        (AUTO,   0x100),
        (0x1000, 0x1000),
    )
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_Mi32InterconnectMatrix()
    print(toRtl(u))
