#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import SwitchLogic
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.hObjList import HObjList
from hwtLib.abstract.busInterconnect import BusInterconnect, AUTO_ADDR
from hwtLib.xilinx.ipif.intf import Ipif
from pyMathBitPrecise.bit_utils import get_bit_range
from hwt.hdl.types.defs import BIT


class IpifInterconnectMatrix(BusInterconnect):
    """
    Simple matrix interconnect for IPIF interface

    .. hwt-autodoc:: _example_IpifInterconnectMatrix
    """

    def _config(self) -> None:
        super(IpifInterconnectMatrix, self)._config()
        Ipif._config(self)

    def _declr(self) -> None:
        self._normalize_config()
        addClkRstn(self)

        slavePorts = HObjList()
        for _ in self.MASTERS:
            s = Ipif()
            s._updateParamsFrom(self)
            slavePorts.append(s)

        self.s = slavePorts

        masterPorts = HObjList()
        for _, size in self.SLAVES:
            m = Ipif()._m()
            m.ADDR_WIDTH = log2ceil(size - 1)
            m.DATA_WIDTH = self.DATA_WIDTH
            masterPorts.append(m)

        self.m = masterPorts

    def _impl(self) -> None:
        if len(self.MASTERS) > 1:
            raise NotImplementedError()

        m = self.s[0]

        wrack = rdack = err = BIT.from_py(0)
        AW = int(self.ADDR_WIDTH)
        rdata = []
        for i, (s, (s_offset, s_size)) in\
                enumerate(zip(self.m, self.SLAVES)):
            s.bus2ip_addr(m.bus2ip_addr, fit=True)
            s.bus2ip_be(m.bus2ip_be)
            s.bus2ip_rnw(m.bus2ip_rnw)
            s.bus2ip_data(m.bus2ip_data)

            bitsOfSubAddr = log2ceil(s_size - 1)
            prefix = get_bit_range(
                s_offset, bitsOfSubAddr, AW - bitsOfSubAddr)
            cs = self._sig(f"m_cs_{i:d}")
            cs(m.bus2ip_addr[AW:bitsOfSubAddr]._eq(prefix))
            s.bus2ip_cs(m.bus2ip_cs & cs)

            err = err | (cs & s.ip2bus_error)
            rdack = rdack | (cs & s.ip2bus_rdack)
            wrack = wrack | (cs & s.ip2bus_wrack)
            rdata.append((cs, s.ip2bus_data))

        m.ip2bus_error(err)
        m.ip2bus_rdack(rdack)
        m.ip2bus_wrack(wrack)

        SwitchLogic(
            [(sel, m.ip2bus_data(data)) for sel, data in rdata],
            default=m.ip2bus_data(None)
        )


def _example_IpifInterconnectMatrix():
    AUTO = AUTO_ADDR
    u = IpifInterconnectMatrix()
    u.MASTERS = (({0, 1, 2, 3}),)
    u.SLAVES = (
        (0x0000, 0x100),
        (0x0100, 0x100),
        (AUTO, 0x100),
        (0x1000, 0x1000),
    )
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_IpifInterconnectMatrix()
    print(to_rtl_str(u))
