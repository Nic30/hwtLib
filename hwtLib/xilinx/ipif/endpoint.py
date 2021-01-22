#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, FsmBuilder
from hwt.hdl.types.enum import HEnum
from hwt.math import inRange
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.xilinx.ipif.intf import Ipif


class IpifEndpoint(BusEndpoint):
    """
    Delegate request from bus to fields of structure

    :attention: interfaces are dynamically generated from names of fileds
        in structure template
    :attention: byte enable and register clock enable signals are ignored

    .. hwt-autodoc:: _example_IpifEndpoint
    """

    _getWordAddrStep = Ipif._getWordAddrStep
    _getAddrStep = Ipif._getAddrStep

    def __init__(self, structTemplate, intfCls=Ipif, shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             intfCls=intfCls,
                             shouldEnterFn=shouldEnterFn)

    def _impl(self):
        self._parseTemplate()
        # build read data output mux

        st_t = HEnum('st_t', ['idle', "writeAck", 'readDelay', 'rdData'])
        ipif = self.bus
        addr = ipif.bus2ip_addr
        ipif.ip2bus_error(0)
        addrVld = ipif.bus2ip_cs

        isInMyAddrSpace = self.isInMyAddrRange(addr)

        st = FsmBuilder(self, st_t)\
        .Trans(st_t.idle,
            (addrVld & isInMyAddrSpace & ipif.bus2ip_rnw, st_t.rdData),
            (addrVld & isInMyAddrSpace & ~ipif.bus2ip_rnw, st_t.writeAck)
        ).Trans(st_t.writeAck,
            st_t.idle
        ).Trans(st_t.readDelay,
            st_t.rdData
        ).Trans(st_t.rdData,
            st_t.idle
        ).stateReg

        wAck = st._eq(st_t.writeAck)
        ipif.ip2bus_rdack(st._eq(st_t.rdData))
        ipif.ip2bus_wrack(wAck)
        ADDR_STEP = self._getAddrStep()
        dataToBus = ipif.ip2bus_data(None)
        for (_, _), t in reversed(self._bramPortMapped):
            # map addr for bram ports
            _addr = t.bitAddr // ADDR_STEP
            _isMyAddr = inRange(addr, _addr, t.bitAddrEnd // ADDR_STEP)
            port = self.getPort(t)

            self.propagateAddr(addr, ADDR_STEP, port.addr,
                               port.dout._dtype.bit_length(), t)

            port.en(_isMyAddr & ipif.bus2ip_cs)
            port.we(_isMyAddr & wAck)

            dataToBus = If(_isMyAddr,
                ipif.ip2bus_data(port.dout)
            ).Else(
                dataToBus
            )

            port.din(ipif.bus2ip_data)

        self.connect_directly_mapped_write(ipif.bus2ip_addr, ipif.bus2ip_data, ~ipif.bus2ip_rnw & wAck)
        self.connect_directly_mapped_read(ipif.bus2ip_addr, ipif.ip2bus_data, dataToBus)


def _example_IpifEndpoint():
    from hwt.hdl.types.struct import HStruct
    from hwtLib.types.ctypes import uint32_t
    u = IpifEndpoint(
            HStruct(
                (uint32_t, "field0"),
                (uint32_t, "field1"),
                (uint32_t[32], "bramMapped")
                ))
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_IpifEndpoint()
    print(to_rtl_str(u))
