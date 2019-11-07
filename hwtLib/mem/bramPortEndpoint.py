#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import c, SwitchLogic, log2ceil, Switch
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import BramPort_withoutClk
from hwtLib.abstract.busEndpoint import BusEndpoint


class BramPortEndpoint(BusEndpoint):
    """
    Delegate transaction from BrapmPort interface to interfaces
    for fields of specified structure.

    :attention: Interfaces are dynamically generated from names
        of fields in structure template.
    
    .. hwt-schematic:: _example_BramPortEndpoint
    """
    _getWordAddrStep = BramPort_withoutClk._getWordAddrStep
    _getAddrStep = BramPort_withoutClk._getAddrStep

    def __init__(self, structTemplate, intfCls=BramPort_withoutClk,
                 shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             intfCls=intfCls, shouldEnterFn=shouldEnterFn)

    def _impl(self):
        self._parseTemplate()
        bus = self.bus

        def connectRegIntfAlways(regIntf, _addr):
            return (
                c(bus.din, regIntf.dout.data) +
                c(bus.we & bus.en & bus.addr._eq(_addr), regIntf.dout.vld)
            )

        ADDR_STEP = self._getAddrStep()
        if self._directlyMapped:
            readReg = self._reg("readReg", dtype=bus.dout._dtype)
            # tuples (condition, assign statements)
            readRegInputs = []
            for t in self._directlyMapped:
                port = self.getPort(t)
                _addr = t.bitAddr // ADDR_STEP
                connectRegIntfAlways(port, _addr)
                readRegInputs.append((bus.addr._eq(_addr),
                                      readReg(port.din)
                                      ))
            SwitchLogic(readRegInputs)
        else:
            readReg = None

        if self._bramPortMapped:
            BRAMS_CNT = len(self._bramPortMapped)
            bramIndxCases = []
            readBramIndx = self._reg("readBramIndx", Bits(
                log2ceil(BRAMS_CNT + 1), False))
            outputSwitch = Switch(readBramIndx)

            for i, t in enumerate(self._bramPortMapped):
                # if we can use prefix instead of addr comparing do it
                _addr = t.bitAddr // ADDR_STEP
                _addrEnd = t.bitAddrEnd // ADDR_STEP
                port = self.getPort(t)

                _addrVld, _ = self.propagateAddr(bus.addr,
                                                 ADDR_STEP,
                                                 port.addr,
                                                 port.dout._dtype.bit_length(),
                                                 t)

                port.we(bus.we & _addrVld & bus.en)
                port.en(bus.en & _addrVld & bus.en)
                port.din(bus.din)

                bramIndxCases.append((_addrVld, readBramIndx(i)))
                outputSwitch.Case(i, bus.dout(port.dout))

            outputSwitch.Default(bus.dout(readReg))
            SwitchLogic(bramIndxCases,
                        default=readBramIndx(BRAMS_CNT))
        else:
            bus.dout(readReg)


def _example_BramPortEndpoint():
    from hwt.hdl.types.struct import HStruct
    from hwtLib.types.ctypes import uint32_t

    u = BramPortEndpoint(
        HStruct(
            (uint32_t, "reg0"),
            (uint32_t, "reg1"),
            (uint32_t[1024], "segment0"),
            (uint32_t[1024], "segment1"),
            (uint32_t[1024 + 4], "nonAligned0")
        )
    )
    u.DATA_WIDTH = 32
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_BramPortEndpoint()
    print(toRtl(u))
