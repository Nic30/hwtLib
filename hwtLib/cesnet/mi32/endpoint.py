#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch, SwitchLogic
from hwt.hdl.types.bits import Bits
from hwt.math import log2ceil
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.cesnet.mi32.intf import Mi32


class Mi32Endpoint(BusEndpoint):
    """
    Delegate request from bus to fields of structure

    :attention: interfaces are dynamically generated from names of fileds
        in structure template
    :attention: byte enable and register clock enable signals are ignored

    .. hwt-autodoc:: _example_Mi32Endpoint
    """

    _getWordAddrStep = Mi32._getWordAddrStep
    _getAddrStep = Mi32._getAddrStep

    def __init__(self, structTemplate, intfCls=Mi32, shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             intfCls=intfCls,
                             shouldEnterFn=shouldEnterFn)

    def _impl(self):
        self._parseTemplate()
        bus = self.bus
        bus.ardy(1)

        ADDR_STEP = self._getAddrStep()
        if self._directly_mapped_words:
            readReg = self._reg("readReg", dtype=bus.drd._dtype)
            # tuples (condition, assign statements)
            If(bus.rd,
               self.connect_directly_mapped_read(bus.addr, readReg, [])
            )
            self.connect_directly_mapped_write(bus.addr, bus.dwr, bus.wr)
        else:
            readReg = None
        rd_delayed = self._reg("rd_delayed", def_val=0)
        rd_delayed(bus.rd & self.isInMyAddrRange(bus.addr))
        if self._bramPortMapped:
            BRAMS_CNT = len(self._bramPortMapped)
            bramIndxCases = []
            readBramIndx = self._reg("readBramIndx", Bits(
                log2ceil(BRAMS_CNT + 1), False))
            outputSwitch = Switch(readBramIndx)

            for i, ((_, _), t) in enumerate(self._bramPortMapped):
                # if we can use prefix instead of addr comparing do it
                _addr = t.bitAddr // ADDR_STEP
                _addrEnd = t.bitAddrEnd // ADDR_STEP
                port = self.getPort(t)

                _addrVld, _ = self.propagateAddr(bus.addr,
                                                 ADDR_STEP,
                                                 port.addr,
                                                 port.dout._dtype.bit_length(),
                                                 t)

                port.we(bus.wr & _addrVld)
                port.en((bus.rd | bus.wr) & _addrVld)
                port.din(bus.dwr)

                bramIndxCases.append((_addrVld, readBramIndx(i)))
                outputSwitch.Case(i, bus.drd(port.dout))

            outputSwitch.Default(bus.drd(readReg))
            SwitchLogic(bramIndxCases,
                        default=readBramIndx(BRAMS_CNT))
        else:
            bus.drd(readReg)
        bus.drdy(rd_delayed)


def _example_Mi32Endpoint():
    from hwt.hdl.types.struct import HStruct
    from hwtLib.types.ctypes import uint32_t
    u = Mi32Endpoint(
            HStruct(
                (uint32_t, "field0"),
                (uint32_t, "field1"),
                #(uint32_t[32], "bramMapped")
                ))
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_Mi32Endpoint()
    print(to_rtl_str(u))
