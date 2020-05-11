#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.enum import HEnum
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from ipCorePackager.constants import DIRECTION


def AxiReaderCore():
    n = RtlNetlist()
    rSt_t = HEnum('rSt_t', ['rdIdle', 'rdData'])

    rSt = n.sig('rSt', rSt_t)
    r_idle = n.sig("r_idle")
    arRd = n.sig('arRd')
    arVld = n.sig('arVld')
    rVld = n.sig('rVld')
    rRd = n.sig('rRd')

    # ar fsm next
    If(arRd,
       # rdIdle
        If(arVld,
           rSt(rSt_t.rdData)
        ).Else(
           rSt(rSt_t.rdIdle)
        )
    ).Else(
        # rdData
        If(rRd & rVld,
           rSt(rSt_t.rdIdle)
        ).Else(
           rSt(rSt_t.rdData)
        )
    )
    r_idle(rSt._eq(rSt_t.rdIdle))
    return n, {
        r_idle: DIRECTION.OUT,
        arRd: DIRECTION.IN,
        arVld: DIRECTION.IN,
        rVld: DIRECTION.IN,
        rRd: DIRECTION.IN
    }


if __name__ == "__main__":
    netlist, interfaces = AxiReaderCore()
    print(netlistToVhdlStr("AxiReaderCore", netlist, interfaces))
