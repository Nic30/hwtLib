#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, FsmBuilder
from hwt.math import inRange
from hwt.hdl.types.enum import HEnum
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.avalon.mm import AvalonMM, RESP_OKAY, RESP_SLAVEERROR


class AvalonMmEndpoint(BusEndpoint):
    """
    Delegate request from bus to fields of structure

    :attention: interfaces are dynamically generated
        from names of fileds in structure template
    :attention: byte enable and register clock enable signals
        are ignored

    .. hwt-autodoc:: _example_AvalonMmEndpoint
    """

    _getWordAddrStep = AvalonMM._getWordAddrStep
    _getAddrStep = AvalonMM._getAddrStep

    def __init__(self, structTemplate, intfCls=AvalonMM, shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             intfCls=intfCls,
                             shouldEnterFn=shouldEnterFn)

    def _impl(self):
        self._parseTemplate()
        # build read data output mux

        st_t = HEnum('st_t', ['idle', 'readDelay', 'rdData'])
        bus = self.bus
        addr = bus.address
        addrVld = bus.read | bus.write

        st = FsmBuilder(self, st_t)\
            .Trans(st_t.idle,
                (addrVld & bus.read, st_t.rdData),
                (addrVld & bus.write, st_t.idle)
            ).Trans(st_t.readDelay,
                st_t.rdData
            ).Trans(st_t.rdData,
                st_t.idle
            ).stateReg

        wAck = True
        wr = bus.write & wAck
        isInAddrRange = (self.isInMyAddrRange(bus.address))

        If(isInAddrRange,
            bus.response(RESP_OKAY)
        ).Else(
            bus.response(RESP_SLAVEERROR)
        )
        bus.waitRequest(bus.read & ~st._eq(st_t.rdData))
        bus.readDataValid(st._eq(st_t.rdData))
        bus.writeResponseValid(wr)

        ADDR_STEP = self._getAddrStep()
        dataToBus = bus.readData(None)
        for (_, _), t in reversed(self._bramPortMapped):
            # map addr for bram ports
            _addr = t.bitAddr // ADDR_STEP
            _isMyAddr = inRange(addr, _addr, t.bitAddrEnd // ADDR_STEP)
            wasMyAddr = self._reg("wasMyAddr")
            If(st._eq(st_t.idle),
                wasMyAddr(_isMyAddr)
            )
            port = self.getPort(t)

            self.propagateAddr(addr, ADDR_STEP, port.addr,
                               port.dout._dtype.bit_length(), t)

            port.en(_isMyAddr & addrVld)
            port.we(_isMyAddr & wr)

            dataToBus = If(wasMyAddr & st._eq(st_t.rdData),
                           bus.readData(port.dout)
                        ).Else(
                            dataToBus
                        )

            port.din(bus.writeData)

        self.connect_directly_mapped_write(addr, bus.writeData, wr)
        self.connect_directly_mapped_read(bus.address, bus.readData, dataToBus)


def _example_AvalonMmEndpoint():
    from hwt.hdl.types.struct import HStruct
    from hwtLib.types.ctypes import uint32_t
    u = AvalonMmEndpoint(
        HStruct(
            (uint32_t, "field0"),
            (uint32_t, "field1"),
            (uint32_t[32], "bramMapped")
        ))
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AvalonMmEndpoint
    print(to_rtl_str(u))
