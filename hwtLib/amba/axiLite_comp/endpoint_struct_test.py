#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.struct import HStruct
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.types.ctypes import uint32_t, uint16_t
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwt.hdl.types.bits import Bits

structHierarchy = HStruct(
                          (HStruct(
                              (uint32_t, "field0"),
                              (uint32_t, "field1")
                          ), "a")
                        )
structHierarchy_str = """\
struct {
    struct {
        <Bits, 32bits, unsigned> field0 // start:0x0(bit) 0x0(byte)
        <Bits, 32bits, unsigned> field1 // start:0x20(bit) 0x4(byte)
    } a // start:0x0(bit) 0x0(byte)
}"""

structHierarchyArr = HStruct(
                             (HStruct(
                                 (uint16_t, "field0"),
                                 (uint16_t, None),
                                 (uint32_t, "field1")
                                 )[3], "a")
                             )
structHierarchyArr_str = """\
struct {
    struct {
        <Bits, 16bits, unsigned> field0 // start:0x0(bit) 0x0(byte)
        //<Bits, 16bits, unsigned> empty space // start:0x10(bit) 0x2(byte)
        <Bits, 32bits, unsigned> field1 // start:0x20(bit) 0x4(byte)
    }[3] a // start:0x0(bit) 0x0(byte)
}"""


class AxiLiteEndpoint_struct_TC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structHierarchy

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(10 * self.CLK)

        self.assertEmpty(u.bus._ag.r.data)
        self.assertEmpty(u.decoded.a.field0._ag.dout)
        self.assertEmpty(u.decoded.a.field1._ag.dout)

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        for _ in range(2):
            r.a.field0.read()
            r.a.field1.read()

        u.decoded.a.field0._ag.din.extend([MAGIC])
        u.decoded.a.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.runSim(30 * self.CLK)

        self.assertValSequenceEqual(u.bus.r._ag.data,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY)])

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, structHierarchy_str)

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        for i in range(2):
            r.a.field0.write(MAGIC + i)
            r.a.field1.write(MAGIC + i + 2)

        self.randomizeAll()
        self.runSim(50 * self.CLK)

        self.assertValSequenceEqual(u.decoded.a.field0._ag.dout,
                                    [MAGIC,
                                     MAGIC + 1
                                     ])
        self.assertValSequenceEqual(u.decoded.a.field1._ag.dout,
                                    [MAGIC + 2,
                                     MAGIC + 3
                                     ])
        self.assertValSequenceEqual(u.bus.b._ag.data, [RESP_OKAY for _ in range(4)])


class AxiLiteEndpoint_arrayStruct_TC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structHierarchyArr

    def mySetUp(self, data_width=32):
        u = AxiLiteEndpoint(self.STRUCT_TEMPLATE,
                shouldEnterFn=lambda x: (True, isinstance(x.dtype, Bits)))
        self.u = u
        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(10 * self.CLK)

        self.assertEmpty(u.bus._ag.r.data)
        for i in range(3):
            self.assertEmpty(u.decoded.a[i].field0._ag.dout)
            self.assertEmpty(u.decoded.a[i].field1._ag.dout)

        with self.assertRaises(IndexError):
            u.decoded.a[3]

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, structHierarchyArr_str)

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        expected = []
        for i in range(2 * 3):
            r.a[i % 3].field0.read()
            expected.append((MAGIC + (i % 3), RESP_OKAY, 16))

            r.a[i % 3].field1.read()
            expected.append((MAGIC + 32 + (i % 3), RESP_OKAY, 32))

        for i in range(3):
            u.decoded.a[i].field0._ag.din.append(MAGIC + i)
            u.decoded.a[i].field1._ag.din.append(MAGIC + 32 + i)

        self.randomizeAll()
        self.runSim(80 * self.CLK)

        readed = u.bus.r._ag.data
        self.assertEqual(len(readed), len(expected))
        for d, ed in zip(readed, expected):
            edata, eresp, ebits = ed
            data, resp = d
            self.assertValEqual(resp, eresp)
            if ebits != 32:
                data = data[ebits:]
            self.assertValEqual(data, edata)

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        r = self.regs
        for i in range(2 * 3):
            d = MAGIC + i
            r.a[i % 3].field0.write(d)

            d = MAGIC + 32 + i
            r.a[i % 3].field1.write(d)

        self.randomizeAll()
        self.runSim(120 * self.CLK)

        for i in range(3):
            self.assertValSequenceEqual(u.decoded.a[i].field0._ag.dout,
                                        [MAGIC + i,
                                         MAGIC + 3 + i
                                         ])
            self.assertValSequenceEqual(u.decoded.a[i].field1._ag.dout,
                                        [MAGIC + 32 + i,
                                         MAGIC + 32 + 3 + i
                                         ])

        self.assertValSequenceEqual(u.bus.b._ag.data,
                                    [RESP_OKAY for _ in range(2 * 2 * 3)])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AxiLiteEndpoint_arrayStruct_TC('test_read'))
    suite.addTest(unittest.makeSuite(AxiLiteEndpoint_struct_TC))
    suite.addTest(unittest.makeSuite(AxiLiteEndpoint_arrayStruct_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
