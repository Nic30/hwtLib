from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.std import BramPort_withoutClk
from hwtLib.amba.axiLite import AxiLite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.constants import RESP_OKAY, RESP_SLVERR
from hwtLib.types.ctypes import uint32_t
from hwt.pyUtils.arrayQuery import flatten
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC, \
    AxiLiteEndpointDenseStartTC, AxiLiteEndpointDenseTC
from hwt.hdlObjects.types.bits import Bits


structTwoArr = HStruct(
                       (uint32_t[4], "field0"),
                       (uint32_t[4], "field1")
                       )

structStructsInArray = HStruct(
                        (HStruct(
                                (uint32_t, "field0"),
                                (uint32_t, "field1")
                                )[4],
                         "arr"),
                        )


def addrGetter(intf):
    if isinstance(intf, AxiLite):
        return intf.ar.addr
    elif isinstance(intf, BramPort_withoutClk):
        return intf.addr
    else:
        raise TypeError(intf)


class AxiLiteEndpointArray(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structTwoArr
    FIELD_ADDR = [0x0, 0x10]

    def test_nop(self):
        u = self.mySetUp(32)
        MAGIC = 100

        for i in range(8):
            u.decoded.field0._ag.mem[i] = MAGIC + 1
            u.decoded.field1._ag.mem[i] = 2 * MAGIC + 1

        self.randomizeAll()
        self.doSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        for i in range(8):
            self.assertValEqual(u.decoded.field0._ag.mem[i], MAGIC + 1)
            self.assertValEqual(u.decoded.field1._ag.mem[i], 2 * MAGIC + 1)

    def test_read(self):
        u = self.mySetUp(32)
        regs = self.regs
        MAGIC = 100

        for i in range(4):
            u.decoded.field0._ag.mem[i] = MAGIC + i + 1
            u.decoded.field1._ag.mem[i] = 2 * MAGIC + i + 1
            regs.field0[i].read()
            regs.field1[i].read()

        self.randomizeAll()
        self.doSim(2 * 8 * 100 * Time.ns)

        self.assertValSequenceEqual(u.bus._ag.r.data, [
            (MAGIC + 1, RESP_OKAY),
            (2 * MAGIC + 1, RESP_OKAY),
            (MAGIC + 2, RESP_OKAY),
            (2 * MAGIC + 2, RESP_OKAY),
            (MAGIC + 3, RESP_OKAY),
            (2 * MAGIC + 3, RESP_OKAY),
            (MAGIC + 4, RESP_OKAY),
            (2 * MAGIC + 4, RESP_OKAY),
            ])

    def test_write(self):
        u = self.mySetUp(32)
        regs = self.regs
        MAGIC = 100

        for i in range(4):
            u.decoded.field0._ag.mem[i] = None
            u.decoded.field1._ag.mem[i] = None
            regs.field0[i].write(MAGIC + i + 1)
            regs.field1[i].write(2 * MAGIC + i + 1)

        self.randomizeAll()
        self.doSim(2 * 8 * 100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        for i in range(4):
            self.assertValEqual(u.decoded.field0._ag.mem[i], MAGIC + i + 1, "index=%d" % i)
            self.assertValEqual(u.decoded.field1._ag.mem[i], 2 * MAGIC + i + 1, "index=%d" % i)

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        expected = """struct {
    <Bits, 32bits, unsigned>[4] field0 // start:0x0(bit) 0x0(byte)
    <Bits, 32bits, unsigned>[4] field1 // start:0x80(bit) 0x10(byte)
}"""
        self.assertEqual(s, expected)


class AxiLiteEndpointStructsInArray(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structStructsInArray

    def mySetUp(self, data_width=32):
        u = AxiLiteEndpoint(self.STRUCT_TEMPLATE,
                            shouldEnterFn=lambda x: (True,
                                                     isinstance(x.dtype, Bits)))
        self.u = u

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.doSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        for item in u.decoded.arr:
            self.assertEmpty(item.field0._ag.dout)
            self.assertEmpty(item.field1._ag.dout)

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        expected = """struct {
    struct {
        <Bits, 32bits, unsigned> field0 // start:0x0(bit) 0x0(byte)
        <Bits, 32bits, unsigned> field1 // start:0x20(bit) 0x4(byte)
    }[4] arr // start:0x0(bit) 0x0(byte)
}"""
        self.assertEqual(s, expected)

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        MAGIC2 = 300

        u.bus.ar._ag.data.extend([i * 0x4 for i in range(4 * 2 + 1)])

        for i, a in enumerate(u.decoded.arr):
            a.field0._ag.din.extend([MAGIC + i])
            a.field1._ag.din.extend([MAGIC2 + i])

        self.randomizeAll()
        self.doSim(500 * Time.ns)
        expected = list(flatten([[(MAGIC + i, RESP_OKAY), (MAGIC2 + i, RESP_OKAY)]
                                 for i in range(4)], level=1)
                        ) + [(None, RESP_SLVERR)]
        self.assertValSequenceEqual(u.bus.r._ag.data, expected)

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        MAGIC2 = 300
        m = mask(32 // 8)
        N = 4

        u.bus.aw._ag.data.extend([i * 0x4 for i in range(N * 2 + 1)])

        expected = [
            [(MAGIC + i + 1, m) for i in range(N)],
            [(MAGIC2 + i + 1, m) for i in range(N)]
            ]

        u.bus.w._ag.data.extend(flatten(zip(expected[0], expected[1]), level=1))
        u.bus.w._ag.data.append((123, m))

        self.randomizeAll()
        self.doSim(800 * Time.ns)

        for i, a in enumerate(u.decoded.arr):
            # [index of field][index in arr][data index]
            self.assertValSequenceEqual(a.field0._ag.dout, [expected[0][i][0]])
            self.assertValSequenceEqual(a.field1._ag.dout, [expected[1][i][0]])

        self.assertValSequenceEqual(u.bus.b._ag.data, [RESP_OKAY for _ in range(2 * N)] + [RESP_SLVERR])

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AxiLiteEndpointArray('test_read'))
    suite.addTest(unittest.makeSuite(AxiLiteEndpointTC))
    suite.addTest(unittest.makeSuite(AxiLiteEndpointDenseStartTC))
    suite.addTest(unittest.makeSuite(AxiLiteEndpointDenseTC))
    suite.addTest(unittest.makeSuite(AxiLiteEndpointArray))
    suite.addTest(unittest.makeSuite(AxiLiteEndpointStructsInArray))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    # u = AxiLiteEndpoint(structStructsInArray, shouldEnterFn=lambda tmpl: True)
    # u.DATA_WIDTH.set(32)
    # print(toRtl(u))
