#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, FsmBuilder, Or, log2ceil, connect, Switch, \
    SwitchLogic
from hwt.hdlObjects.typeShortcuts import vec, vecT
from hwt.hdlObjects.types.enum import Enum
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.amba.axiLite import AxiLite
from hwtLib.amba.constants import RESP_OKAY, RESP_SLVERR


class AxiLiteEndpoint(BusEndpoint):
    """
    Delegate request from AxiLite interface to fields of structure
    write has higher priority
    """
    _getWordAddrStep = AxiLite._getWordAddrStep
    _getAddrStep = AxiLite._getAddrStep

    def __init__(self, structTemplate, intfCls=AxiLite, shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             intfCls=intfCls,
                             shouldEnterFn=shouldEnterFn)

    def readPart(self, awAddr, w_hs):
        ADDR_STEP = self._getAddrStep()
        # build read data output mux
        r = self.bus.r
        ar = self.bus.ar
        rSt_t = Enum('rSt_t', ['rdIdle', 'bramRd', 'rdData'])
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
        ar.ready ** (arRd & ~w_hs)

        # save ar addr
        arAddr = self._reg('arAddr', ar.addr._dtype)
        If(ar.valid & arRd,
            arAddr ** ar.addr
        )

        isInAddrRange = self.isInMyAddrRange(arAddr)
        r.valid ** rSt._eq(rSt_t.rdData)
        If(isInAddrRange,
            r.resp ** RESP_OKAY
        ).Else(
            r.resp ** RESP_SLVERR
        )
        if self._bramPortMapped:
            rdataReg = self._reg("rdataReg", r.data._dtype)
            _isInBramFlags = []
            # list of tuples (cond, rdataReg assignment)
            rregCases = []
            # index of bram from where we reads from
            bramRdIndx = self._reg("bramRdIndx", vecT(log2ceil(len(self._bramPortMapped))))
            bramRdIndxSwitch = Switch(bramRdIndx)
            for bramIndex, t in enumerate(self._bramPortMapped):
                port = self.getPort(t)

                # map addr for bram ports
                dstAddrStep = port.dout._dtype.bit_length()
                (_isMyArAddr, arAddrConnect) = self.propagateAddr(ar.addr, ADDR_STEP, port.addr, dstAddrStep, t)
                (_, ar2AddrConnect) = self.propagateAddr(arAddr, ADDR_STEP, port.addr, dstAddrStep, t)
                (_isMyAwAddr, awAddrConnect) = self.propagateAddr(awAddr, ADDR_STEP, port.addr, dstAddrStep, t)
                prioritizeWrite = _isMyAwAddr & w_hs

                If(prioritizeWrite,
                    awAddrConnect
                ).Elif(rSt._eq(rSt_t.rdIdle),
                    arAddrConnect
                ).Else(
                    ar2AddrConnect
                )
                _isInBramFlags.append(_isMyArAddr)

                port.en ** ((_isMyArAddr & ar.valid) | prioritizeWrite)
                port.we ** prioritizeWrite

                rregCases.append((_isMyArAddr, bramRdIndx ** bramIndex))
                bramRdIndxSwitch.Case(bramIndex, rdataReg ** port.dout)

            bramRdIndxSwitch.Default(rdataReg ** rdataReg)
            If(arRd,
               SwitchLogic(rregCases)
            )
            isBramAddr ** Or(*_isInBramFlags)

        else:
            rdataReg = None
            isBramAddr ** 0

        SwitchLogic([(arAddr._eq(t.bitAddr // ADDR_STEP),
                      r.data ** self.getPort(t).din)
                     for t in self._directlyMapped],
                    default=r.data ** rdataReg)

    def writeRespPart(self, wAddr, respVld):
        b = self.bus.b

        isInAddrRange = (self.isInMyAddrRange(wAddr))

        If(isInAddrRange,
           b.resp ** RESP_OKAY
        ).Else(
           b.resp ** RESP_SLVERR
        )
        b.valid ** respVld

    def writePart(self):
        sig = self._sig
        reg = self._reg
        addrWidth = evalParam(self.ADDR_WIDTH).val
        ADDR_STEP = self._getAddrStep()

        wSt_t = Enum('wSt_t', ['wrIdle', 'wrData', 'wrResp'])
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
        aw.ready ** awRd
        aw_hs = awRd & aw.valid

        wRd = wSt._eq(wSt_t.wrData)
        w.ready ** wRd

        w_hs ** (w.valid & wRd)

        # save aw addr
        If(aw_hs,
            awAddr ** aw.addr
        ).Else(
            awAddr ** awAddr
        )

        # output vld
        for t in self._directlyMapped:
            out = self.getPort(t).dout
            connect(w.data, out.data, fit=True)
            out.vld ** (w_hs & (awAddr._eq(vec(t.bitAddr // ADDR_STEP, addrWidth))))

        for t in self._bramPortMapped:
            din = self.getPort(t).din
            connect(w.data, din, fit=True)

        self.writeRespPart(awAddr, wSt._eq(wSt_t.wrResp))

        return awAddr, w_hs

    def _impl(self):
        self._parseTemplate()
        awAddr, w_hs = self.writePart()
        self.readPart(awAddr, w_hs)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwt.hdlObjects.types.array import Array
    from hwt.hdlObjects.types.struct import HStruct
    from hwtLib.types.ctypes import uint32_t

    u = AxiLiteEndpoint(
            HStruct(
                (Array(uint32_t, 4), "field0"),
                # (Array(uint32_t, 2), "field1"),
                (Array(uint32_t, 4), "field2")
                # (uint32_t, "data0"),
                # (uint32_t, "data1"),
                # (Array(uint32_t, 32), "bramMapped")
                )
            )
    u.ADDR_WIDTH.set(8)
    u.DATA_WIDTH.set(32)

    print(toRtl(u))
