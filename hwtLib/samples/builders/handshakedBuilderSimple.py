#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.handshaked.builder import HsBuilder


class HandshakedBuilderSimple(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = Handshaked()
        self.b = Handshaked()

    def _impl(self):
        b = HsBuilder(self, self.a)

        b.buff()
        b.buff(items=16)
        b.buff(latency=2, delay=1)

        self.b ** b.end


class HandshakedBuilderSimpleTC(SimTestCase):
    def test_passData(self):
        u = HandshakedBuilderSimple()
        self.prepareUnit(u)

        u.a._ag.data.extend([1, 2, 3, 4])

        self.doSim(200 * Time.ns)

        self.assertValSequenceEqual(u.b._ag.data, [1, 2, 3, 4])


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(HandshakedBuilderSimple()))
