#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, FsmBuilder, Switch
from hwt.hdl.types.enum import HEnum
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.ipif.intf import Ipif


class IpifEndpoint(BusEndpoint):
    """
    Delegate request from bus to fields of structure

    :attention: interfaces are dynamically generated from names of fileds
        in structure template
    :attention: byte enable and register clock enable signals are ignored

    .. hwt-schematic:: _example_IpifEndpoint
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

        def isMyAddr(addrSig, addr, end):
            return (addrSig >= addr) & (addrSig < end)

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
        for t in reversed(self._bramPortMapped):
            # map addr for bram ports
            _addr = t.bitAddr // ADDR_STEP
            _isMyAddr = isMyAddr(addr, _addr, t.bitAddrEnd // ADDR_STEP)
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

        for t in self._directlyMapped:
            _addr = t.bitAddr // ADDR_STEP
            port = self.getPort(t)

            port.dout.vld(addr._eq(_addr) & ~ipif.bus2ip_rnw & wAck)
            port.dout.data(ipif.bus2ip_data)

        _isInBramFlags = []
        Switch(ipif.bus2ip_addr)\
        .addCases(
                [(t.bitAddr // ADDR_STEP, ipif.ip2bus_data(self.getPort(t).din))
                 for t in self._directlyMapped]
        ).Default(
            dataToBus
        )


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
    from hwt.synthesizer.utils import toRtl
    u = _example_IpifEndpoint()
    print(toRtl(u))
