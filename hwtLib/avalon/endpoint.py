#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.math import inRange
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

    def __init__(self, structTemplate, hwIOCls=AvalonMM, shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             hwIOCls=hwIOCls,
                             shouldEnterFn=shouldEnterFn)

    def hwImpl(self):
        self._parseTemplate()
        # build read data output mux

        bus = self.bus
        addr = bus.address
        addrVld = bus.read | bus.write

        wr = bus.write
        isInAddrRange = self.isInMyAddrRange(bus.address)

        wasInAddrRange = self._reg("wasInAddrRange")
        wasWr = self._reg("wasWr", def_val=0)
        rReq = self._reg("rReq", def_val=0)
        rAddr = self._reg("rAddr", dtype=addr._dtype)
        rReq(bus.read)
        wasInAddrRange(isInAddrRange)
        wasWr(wr)
        If(bus.read,
           rAddr(addr),
        )
        
        If(wasInAddrRange,
            bus.response(RESP_OKAY)
        ).Else(
            bus.response(RESP_SLAVEERROR)
        )
        bus.waitRequest(0)
        bus.readDataValid(rReq)
        bus.writeResponseValid(wasWr)

        ADDR_STEP = self._getAddrStep()
        dataToBus = bus.readData(None)
        for (_, _), t in reversed(self._bramPortMapped):
            # map addr for bram ports
            _addr = t.bitAddr // ADDR_STEP
            _isMyAddr = inRange(addr, _addr, t.bitAddrEnd // ADDR_STEP)
            wasMyAddr = self._reg("wasMyAddr")
            wasMyAddr(_isMyAddr)
            
            port = self.getPort(t)

            self.propagateAddr(addr, ADDR_STEP, port.addr,
                               port.dout._dtype.bit_length(), t)

            port.en(_isMyAddr & addrVld)
            port.we(_isMyAddr & wr)

            dataToBus = If(wasMyAddr,
                            bus.readData(port.dout)
                        ).Else(
                            dataToBus
                        )

            port.din(bus.writeData)

        self.connect_directly_mapped_write(addr, bus.writeData, wr)
        self.connect_directly_mapped_read(rAddr, bus.readData, dataToBus)

def _example_AvalonMmEndpoint():
    from hwt.hdl.types.struct import HStruct
    from hwtLib.types.ctypes import uint32_t
    m = AvalonMmEndpoint(
        HStruct(
            (uint32_t, "field0"),
            (uint32_t, "field1"),
            (uint32_t[32], "bramMapped")
        ))
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_AvalonMmEndpoint
    print(to_rtl_str(n))
