#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch
from hwt.hdl.types.enum import HEnum
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from ipCorePackager.constants import DIRECTION


def ComplexConditions():
    n = RtlNetlist()
    stT = HEnum('t_state', ["idle", "tsWait", "ts0Wait", "ts1Wait", "lenExtr"])
    clk = n.sig('clk')
    rst = n.sig("rst")

    st = n.sig('st', stT, clk=clk, syncRst=rst, def_val=stT.idle)
    s_idle = n.sig('s_idle')
    sd0 = n.sig('sd0')
    sd1 = n.sig('sd1')
    cntrlFifoVld = n.sig('ctrlFifoVld')
    cntrlFifoLast = n.sig('ctrlFifoLast')

    def tsWaitLogic(ifNoTsRd):
        return If(sd0 & sd1,
                   st(stT.lenExtr)
               ).Elif(sd0,
                   st(stT.ts1Wait)
               ).Elif(sd1,
                   st(stT.ts0Wait)
               ).Else(
                   ifNoTsRd
               )
    Switch(st)\
    .Case(stT.idle,
        tsWaitLogic(
            If(cntrlFifoVld,
               st(stT.tsWait)
            )
        )
    ).Case(stT.tsWait,
        tsWaitLogic(st(st))
    ).Case(stT.ts0Wait,
        If(sd0,
           st(stT.lenExtr)
        )
    ).Case(stT.ts1Wait,
        If(sd1,
           st(stT.lenExtr)
        )
    ).Case(stT.lenExtr,
        If(cntrlFifoVld & cntrlFifoLast,
           st(stT.idle)
        )
    )
    s_idle(st._eq(stT.idle))

    return n, {
        rst: DIRECTION.IN,
        clk: DIRECTION.IN,
        sd0: DIRECTION.IN,
        sd1: DIRECTION.IN,
        cntrlFifoVld: DIRECTION.IN,
        cntrlFifoLast: DIRECTION.IN,
        s_idle: DIRECTION.OUT
    }


if __name__ == "__main__":
    netlist, interfaces = ComplexConditions()
    print(netlistToVhdlStr("ComplexConditions", netlist, interfaces))
