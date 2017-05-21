#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import c, SwitchLogic, log2ceil, Switch
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array
from hwt.interfaces.std import BramPort_withoutClk
from hwtLib.abstract.busConverter import BusConverter, inRange


class BramPortEndpoint(BusConverter):
    """
    Delegate transaction from BrapmPort interface to interfaces for fields of specified structure

    :attention: interfaces are dynamically generated from names of fields in structure template
    """
    _getWordAddrStep = BramPort_withoutClk._getWordAddrStep
    _getAddrStep = BramPort_withoutClk._getAddrStep

    def __init__(self, structTemplate, offset=0, intfCls=BramPort_withoutClk):
        BusConverter.__init__(self, structTemplate, offset, intfCls)

    def _impl(self):
        bus = self.bus

        def connectRegIntfAlways(regIntf, _addr):
            return (
                    c(bus.din, regIntf.dout.data) + 
                    c(bus.we & bus.en & bus.addr._eq(_addr), regIntf.dout.vld)
                   )

        def connectBramPortAlways(bramPort, addrOffset, size, _addrVld):
            # explicit signal because vhdl cannot index the result of a type conversion
            # [TODO] port._addrSpaceItem.getMyAddrPrefix()
            addr_tmp = self._sig(bramPort._name + "_addr_tmp", vecT(self.ADDR_WIDTH))
            c(bus.addr - addrOffset, addr_tmp)

            return (
                c(addr_tmp, bramPort.addr, fit=True) + 
                c(bus.we & _addrVld, bramPort.we) + 
                c(bus.en & _addrVld, bramPort.en) + 
                c(bus.din, bramPort.din))
            

        
        if self._directlyMapped:
            readReg = self._reg("readReg", dtype=bus.dout._dtype)
            # tuples (condition, assign statements)
            readRegInputs = []
            for ai in self._directlyMapped:
                connectRegIntfAlways(ai.port, ai.addr)
                readRegInputs.append((bus.addr._eq(ai.addr),
                                      readReg ** ai.port.din
                                      ))
            SwitchLogic(readRegInputs)
        else:
            readReg = None

        if self._bramPortMapped:
            BRAMS_CNT = len(self._bramPortMapped)
            bramIndxCases = []
            readBramIndx = self._reg("readBramIndx", vecT(log2ceil(BRAMS_CNT + 1), False))
            outputSwitch = Switch(readBramIndx)
            
            for i, ai in enumerate(self._bramPortMapped):
                # if we can use prefix instead of addr comparing do it
                tmp = ai.port._addrSpaceItem.getMyAddrPrefix()
                if tmp is None:
                    _addrVld = inRange(bus.addr, ai.addr, ai.size)
                else:
                    prefix, subaddrBits = tmp
                    _addrVld = bus.addr[:subaddrBits]._eq(prefix)
    
                connectBramPortAlways(ai.port, ai.addr, ai.size, _addrVld & bus.en)
                bramIndxCases.append((_addrVld, readBramIndx ** i))
                outputSwitch.Case(i, bus.dout ** ai.port.dout)

            outputSwitch.Default(bus.dout ** readReg)    
            SwitchLogic(bramIndxCases, default=readBramIndx ** BRAMS_CNT)
        else:
            bus.dout ** readReg

if __name__ == "__main__":
    from hwt.hdlObjects.types.struct import HStruct
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.types.ctypes import uint32_t

    u = BramPortEndpoint(
            HStruct(
                (uint32_t, "reg0"),
                (uint32_t, "reg1"),
                (Array(uint32_t, 1024), "segment0"),
                (Array(uint32_t, 1024), "segment1"),
                (Array(uint32_t, 1024 + 4), "nonAligned0")
                )
            )
    u.DATA_WIDTH.set(32)
    print(toRtl(u))
