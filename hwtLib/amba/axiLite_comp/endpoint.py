#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

from hwt.code import If, FsmBuilder, Or, Switch, SwitchLogic
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.hdl.value import HValue
from hwt.math import log2ceil
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.constants import RESP_OKAY, RESP_SLVERR


class AxiLiteEndpoint(BusEndpoint):
    """
    Delegate request from AxiLite interface to fields of structure
    write has higher priority.

    .. hwt-autodoc:: _example_AxiLiteEndpoint
    """
    _getWordAddrStep = Axi4Lite._getWordAddrStep
    _getAddrStep = Axi4Lite._getAddrStep

    def __init__(self, structTemplate, intfCls=Axi4Lite, shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             intfCls=intfCls,
                             shouldEnterFn=shouldEnterFn)

    def driveResp(self, isInAddrRange: Union[RtlSignalBase, HValue], resp: RtlSignalBase):
        if isinstance(isInAddrRange, RtlSignalBase):
            return If(isInAddrRange,
               resp(RESP_OKAY)
            ).Else(
               resp(RESP_SLVERR)
            )
        else:
            assert isInAddrRange
            return resp(RESP_OKAY)

    def readPart(self, awAddr, w_hs):
        ADDR_STEP = self._getAddrStep()
        # build read data output mux
        r = self.bus.r
        ar = self.bus.ar
        rSt_t = HEnum('rSt_t', ['rdIdle', 'bramRd', 'rdData'])
        isBramAddr = self._sig("isBramAddr")

        rSt = FsmBuilder(self, rSt_t, stateRegName='rSt')\
        .Trans(rSt_t.rdIdle,
            (ar.valid & ~isBramAddr & ~w_hs, rSt_t.rdData),
            (ar.valid & isBramAddr & ~w_hs, rSt_t.bramRd)
        ).Trans(rSt_t.bramRd,
            (~w_hs, rSt_t.rdData)
        ).Trans(rSt_t.rdData,
            (r.ready, rSt_t.rdIdle)
        ).stateReg

        arRd = rSt._eq(rSt_t.rdIdle)
        ar.ready(arRd & ~w_hs)

        # save ar addr
        arAddr = self._reg('arAddr', ar.addr._dtype)
        If(ar.valid & arRd,
            arAddr(ar.addr)
        )

        isInAddrRange = self.isInMyAddrRange(arAddr)
        r.valid(rSt._eq(rSt_t.rdData))
        self.driveResp(isInAddrRange, r.resp)
        if self._bramPortMapped:
            rdataReg = self._reg("rdataReg", r.data._dtype)
            _isInBramFlags = []
            # list of tuples (cond, rdataReg assignment)
            rregCases = []
            # index of bram from where we reads from
            bramRdIndx = self._reg("bramRdIndx", Bits(
                log2ceil(len(self._bramPortMapped))))
            bramRdIndxSwitch = Switch(bramRdIndx)
            for bramIndex, ((base, end), t) in enumerate(self._bramPortMapped):
                port = self.getPort(t)

                # map addr for bram ports
                dstAddrStep = port.dout._dtype.bit_length()
                (_isMyArAddr, arAddrConnect) = self.propagateAddr(
                    ar.addr, ADDR_STEP, port.addr, dstAddrStep, t)
                (_, ar2AddrConnect) = self.propagateAddr(
                    arAddr, ADDR_STEP, port.addr, dstAddrStep, t)
                (_isMyAwAddr, awAddrConnect) = self.propagateAddr(
                    awAddr, ADDR_STEP, port.addr, dstAddrStep, t)
                prioritizeWrite = w_hs & _isMyAwAddr

                If(prioritizeWrite,
                    awAddrConnect
                ).Elif(rSt._eq(rSt_t.rdIdle),
                    arAddrConnect
                ).Else(
                    ar2AddrConnect
                )
                _isInBramFlags.append(_isMyArAddr)

                port.en((ar.valid & _isMyArAddr) | prioritizeWrite)
                port.we(prioritizeWrite)

                rregCases.append((_isMyArAddr, bramRdIndx(bramIndex)))
                bramRdIndxSwitch.Case(bramIndex, rdataReg(port.dout))

            bramRdIndxSwitch.Default(rdataReg(rdataReg))
            If(arRd,
               SwitchLogic(rregCases)
            )
            isBramAddr(Or(*_isInBramFlags))

        else:
            rdataReg = None
            isBramAddr(0)

        self.connect_directly_mapped_read(arAddr, r.data, r.data(rdataReg))

    def writeRespPart(self, wAddr, respVld):
        b = self.bus.b
        isInAddrRange = self.isInMyAddrRange(wAddr)
        self.driveResp(isInAddrRange, b.resp)
        b.valid(respVld)

    def writePart(self):
        sig = self._sig
        reg = self._reg

        wSt_t = HEnum('wSt_t', ['wrIdle', 'wrData', 'wrResp'])
        aw = self.bus.aw
        w = self.bus.w
        b = self.bus.b

        # write fsm
        wSt = FsmBuilder(self, wSt_t, "wSt")\
            .Trans(wSt_t.wrIdle,
                (aw.valid, wSt_t.wrData)
            ).Trans(wSt_t.wrData,
                (w.valid, wSt_t.wrResp)
            ).Trans(wSt_t.wrResp,
                (b.ready, wSt_t.wrIdle)
           ).stateReg

        awAddr = reg('awAddr', aw.addr._dtype)
        w_hs = sig('w_hs')

        awRd = wSt._eq(wSt_t.wrIdle)
        aw.ready(awRd)
        aw_hs = awRd & aw.valid

        wRd = wSt._eq(wSt_t.wrData)
        w.ready(wRd)

        w_hs(w.valid & wRd)

        # save aw addr
        If(aw_hs,
            awAddr(aw.addr)
        ).Else(
            awAddr(awAddr)
        )
        self.connect_directly_mapped_write(awAddr, w.data, w_hs)
        for (_, _), t in self._bramPortMapped:
            # en, we handled in readPart
            din = self.getPort(t).din
            din(w.data, fit=True)

        self.writeRespPart(awAddr, wSt._eq(wSt_t.wrResp))

        return awAddr, w_hs

    def _impl(self):
        self._parseTemplate()
        awAddr, w_hs = self.writePart()
        self.readPart(awAddr, w_hs)


def _example_AxiLiteEndpoint():
    from hwt.hdl.types.struct import HStruct
    from hwtLib.types.ctypes import uint32_t, uint16_t

    t = HStruct(
        (uint32_t[4], "data0"),
        # optimized address selection because data are aligned
        (uint32_t[4], "data1"),
        (uint32_t[2], "data2"),
        (uint32_t, "data3"),
        # padding
        (uint32_t[32], None),
        # type can be any type
        (HStruct(
            (uint16_t, "data4a"),
            (uint16_t, "data4b"),
            (uint32_t, "data4c")
        ), "data4"),
    )
    u = AxiLiteEndpoint(t)

    # configuration
    u.ADDR_WIDTH = 8
    u.DATA_WIDTH = 32
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiLiteEndpoint()

    print(to_rtl_str(u))
    print(u.bus)
    print(u.decoded.data3)
    print(u.decoded.data4)
