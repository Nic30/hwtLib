#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.frameForge import AxiS_frameForge
from hwt.hdlObjects.types.struct import HStruct
from hwtLib.types.ctypes import uint64_t, uint32_t
from hwtLib.amba.axis import AxiStream
from hwt.bitmask import mask

s1field = HStruct(
    (uint64_t, "item0")
    )

s3field = HStruct(
    (uint64_t, "item0"),
    (uint64_t, "item1"),
    (uint64_t, "item2")
    )

s1field_composit0 = HStruct(
    (uint32_t, "item0"), (uint32_t, "item1"),
    )


class AxiS_frameForge_TC(SimTestCase):
    def instantiateFrameForge(self, structT, DATA_WIDTH=64, randomized=True):
        u = self.u = AxiS_frameForge(AxiStream, structT)
        self.DATA_WIDTH = 64
        u.DATA_WIDTH.set(self.DATA_WIDTH)
        
        self.prepareUnit(self.u)
        if randomized:
            for intf in u._interfaces:
                if intf not in [u.clk, u.rst_n]:
                    self.randomize(intf)

    def test_nop1Field(self, randomized=False):
        self.instantiateFrameForge(s1field, randomized=randomized)
        u = self.u
        t = 100
        if randomized:
            t *= 2 
            
        self.doSim(t * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_1Field(self, randomized=False):
        self.instantiateFrameForge(s1field, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.item0._ag.data.append(MAGIC)
        
        t = 100
        if randomized:
            t *= 2 
            
        self.doSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, mask(self.DATA_WIDTH // 8), 1)])

    def test_1Field_composit0(self, randomized=False):
        self.instantiateFrameForge(s1field_composit0, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.item0._ag.data.append(MAGIC)
        u.item1._ag.data.append(MAGIC + 1)
        
        t = 100
        if randomized:
            t *= 2 
            
        self.doSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(((MAGIC + 1) << 32) | MAGIC, mask(self.DATA_WIDTH // 8), 1)])

    def test_3Fields(self, randomized=False):
        self.instantiateFrameForge(s3field, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.item0._ag.data.append(MAGIC)
        u.item1._ag.data.append(MAGIC + 1)
        u.item2._ag.data.append(MAGIC + 2)
        t = 200
        if randomized:
            t *= 2 
        self.doSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 1),
                                     ])


    def test_r_nop1Field(self):
        self.test_nop1Field(randomized=True)

    def test_r_1Field(self):
        self.test_1Field(randomized=True)

    def test_r_3Fields(self):
        self.test_3Fields(randomized=True)

    def test_r_test_1Field_composit0(self):
        self.test_1Field_composit0(randomized=True)

    def test_3Fields_outOccupiedAtStart(self):
        u = self.u = AxiS_frameForge(AxiStream, s3field)
        self.DATA_WIDTH = 64
        u.DATA_WIDTH.set(self.DATA_WIDTH)
        
        self.prepareUnit(self.u)
        def enDataOut(s):
            u.dataOut._ag.enable = False
            yield s.wait(50 * Time.ns)
            u.dataOut._ag.enable = True
        self.procs.append(enDataOut)
        
        MAGIC = 468
        u.item0._ag.data.append(MAGIC)
        u.item1._ag.data.append(MAGIC + 1)
        u.item2._ag.data.append(MAGIC + 2)
        
        t = 200
        self.doSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 1),
                                     ])

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_resizer_downscale_TC('test_noPass'))
    suite.addTest(unittest.makeSuite(AxiS_frameForge_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
