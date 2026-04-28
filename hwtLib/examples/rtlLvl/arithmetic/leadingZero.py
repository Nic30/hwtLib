#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from ipCorePackager.constants import DIRECTION


def LeadingOne():
    width = 8
    t = HBits(width)
    resT = HBits(4)
    n = RtlNetlist()

    s_in = n.sig("s_in", t)
    index = n.sig("s_leadingOneCnt", resT)

    leadingZeroTop = index(width)
    for i in range(width):
        # iterate from MSB->LSB on first bit 0 set result
        # to number of 1 seen so far
        c = s_in[i]._eq(0)
        leadingZeroTop = If(c,
            index(width - i - 1)
        ).Else(
           leadingZeroTop
        )

    interf = {s_in: DIRECTION.IN, index: DIRECTION.OUT}

    return n, interf


def LeadingOneB():
    width = 8
    t = HBits(width)
    resT = HBits(4)
    n = RtlNetlist()

    s_in = n.sig("s_in", t)
    index = n.sig("s_leadingOneCnt", resT)

    leadingZeroTop = index(width)
    for i in reversed(range(width)):
        # iterate from MSB->LSB on first bit 0 set result
        # to number of 1 seen so far
        c = s_in[width - i - 1]._eq(0)
        leadingZeroTop = If(c,
           index(i)
        ).Else(
           leadingZeroTop
        )

    interf = {s_in: DIRECTION.IN, index: DIRECTION.OUT}

    return n, interf


def LeadingZero():
    width = 8
    t = HBits(width)
    resT = HBits(4)
    n = RtlNetlist()

    s_in = n.sig("s_in", t)
    index = n.sig("s_leadingZeroCnt", resT)

    leadingZeroTop = index(width)
    for i in range(width):
        # iterate from MSB->LSB on first bit 0 set result
        # to number of 1 seen so far
        c = s_in[i]
        leadingZeroTop = If(c,
            index(width - i - 1)
        ).Else(
           leadingZeroTop
        )

    interf = {s_in: DIRECTION.IN, index: DIRECTION.OUT}

    return n, interf


if __name__ == "__main__":
    netlist, interfaces = LeadingOne()
    print(netlistToVhdlStr("LeadingOne", netlist, interfaces))
    netlist, interfaces = LeadingOneB()
    print(netlistToVhdlStr("LeadingOneB", netlist, interfaces))
    netlist, interfaces = LeadingZero()
    print(netlistToVhdlStr("LeadingZero", netlist, interfaces))
