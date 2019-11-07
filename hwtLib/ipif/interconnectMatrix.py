#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, connect, SwitchLogic
from hwt.hdl.typeShortcuts import hBit
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwtLib.abstract.busInterconnect import BusInterconnect, ACCESS_RW, \
    AUTO_ADDR
from hwtLib.ipif.intf import Ipif
from pyMathBitPrecise.bit_utils import selectBitRange


class IpifInterconnectMatrix(BusInterconnect):
    """
    Simple matrix interconnect for IPIF interface

    .. hwt-schematic:: _example_IpifInterconnectMatrix
    """

    def _config(self) -> None:
        Ipif._config(self)

    def _declr(self) -> None:
        addClkRstn(self)

        slavePorts = HObjList()
        for _, features in self._masters:
            if features is not ACCESS_RW:
                raise NotImplementedError(features)
            m = Ipif()
            m._updateParamsFrom(self)
            slavePorts.append(m)

        self.s = slavePorts

        masterPorts = HObjList()
        for _, size, features in self._slaves:
            if features is not ACCESS_RW:
                raise NotImplementedError(features)
            s = Ipif()._m()
            s.ADDR_WIDTH = log2ceil(size - 1)
            s.DATA_WIDTH = self.DATA_WIDTH
            masterPorts.append(s)

        self.m = masterPorts

    def _impl(self) -> None:
        if len(self._masters) > 1:
            raise NotImplementedError()

        m_offset, _ = self._masters[0]
        if m_offset != 0:
            raise NotImplementedError()

        m = self.s[0]

        err = hBit(0)
        rdack = hBit(0)
        wrack = hBit(0)
        AW = int(self.ADDR_WIDTH)
        wdata = []
        for i, (s, (s_offset, s_size, _)) in\
                enumerate(zip(self.m, self._slaves)):
            connect(m.bus2ip_addr, s.bus2ip_addr, fit=True)
            s.bus2ip_be(m.bus2ip_be)
            s.bus2ip_rnw(m.bus2ip_rnw)
            s.bus2ip_data(m.bus2ip_data)

            bitsOfSubAddr = log2ceil(s_size - 1)
            prefix = selectBitRange(
                s_offset, bitsOfSubAddr, AW - bitsOfSubAddr)
            cs = self._sig("m_cs_%d" % i)
            cs(m.bus2ip_addr[AW:bitsOfSubAddr]._eq(prefix))
            s.bus2ip_cs(m.bus2ip_cs & cs)

            err = err | (cs & s.ip2bus_error)
            rdack = rdack | (cs & s.ip2bus_rdack)
            wrack = wrack | (cs & s.ip2bus_wrack)
            wdata.append((cs, s.ip2bus_data))

        m.ip2bus_error(err)
        m.ip2bus_rdack(rdack)
        m.ip2bus_wrack(wrack)

        SwitchLogic(
            [(sel, m.ip2bus_data(data)) for sel, data in wdata],
            default=m.ip2bus_data(None)
        )


def _example_IpifInterconnectMatrix():
    RW = ACCESS_RW
    AUTO = AUTO_ADDR
    u = IpifInterconnectMatrix(
        masters=[(0x0, RW)],
        slaves=[
            (0x0000, 0x100, RW),
            (0x0100, 0x100, RW),
            (AUTO, 0x100, RW),
            (0x1000, 0x1000, RW),
        ]
    )
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_IpifInterconnectMatrix()
    print(toRtl(u))
