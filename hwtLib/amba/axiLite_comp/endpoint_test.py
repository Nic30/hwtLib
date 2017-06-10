from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.struct import HStruct
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.constants import RESP_OKAY, RESP_SLVERR
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster
from hwtLib.types.ctypes import uint32_t
from hwtLib.amba.axiLite import AxiLite
from hwt.interfaces.std import BramPort_withoutClk


structTwoFields = HStruct(
                          (uint32_t, "field0"),
                          (uint32_t, "field1")
                          )
structTwoFieldsDense = HStruct(
                          (uint32_t, "field0"),
                          (uint32_t, None),
                          (uint32_t, "field1")
                          )
structTwoFieldsDenseStart = HStruct(
                          (uint32_t, None),
                          (uint32_t, "field0"),
                          (uint32_t, "field1")
                          )

structTwoArr = HStruct(
                       (Array(uint32_t, 4), "field0"),
                       (Array(uint32_t, 4), "field1")
                       )

structStructsInArray = HStruct(
                        (Array(HStruct(
                                (uint32_t, "field0"),
                                (uint32_t, "field1")),
                              4), "arr"),
                        )


def addrGetter(intf):
    if isinstance(intf, AxiLite):
        return intf.ar.addr
    elif isinstance(intf, BramPort_withoutClk):
        return intf.addr
    else:
        raise TypeError(intf)


class AxiLiteEndpointTC(SimTestCase):
    STRUCT_TEMPLATE = structTwoFields
    FIELD_ADDR = [0x0, 0x4]

    def mkRegisterMap(self, u):
        registerMap = AddressSpaceProbe(u.bus, addrGetter).discover()
        self.registerMap = registerMap
        self.regs = AxiLiteMemSpaceMaster(u.bus, registerMap)

    def randomizeAll(self):
        u = self.u
        for intf in u._interfaces:
            if u not in (u.clk, u.rst_n, u.bus) and not isinstance(intf, BramPort_withoutClk):
                self.randomize(intf)

        self.randomize(u.bus.ar)
        self.randomize(u.bus.aw)
        self.randomize(u.bus.r)
        self.randomize(u.bus.w)
        self.randomize(u.bus.b)

    def mySetUp(self, data_width=32):
        u = self.u = AxiLiteEndpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.doSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        self.assertEmpty(u.decoded.field0._ag.dout)
        self.assertEmpty(u.decoded.field1._ag.dout)

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR
        u.bus.ar._ag.data.extend([A[0], A[1], A[0], A[1], A[1] + 0x4])

        u.decoded.field0._ag.din.extend([MAGIC])
        u.decoded.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.doSim(300 * Time.ns)

        self.assertValSequenceEqual(u.bus.r._ag.data,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (None, RESP_SLVERR)])

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        m = mask(32 // 8)
        A = self.FIELD_ADDR
        u.bus.aw._ag.data.extend([A[0],
                                  A[1],
                                  A[0],
                                  A[1],
                                  A[1] + 0x4])
        u.bus.w._ag.data.extend([(MAGIC, m),
                                 (MAGIC + 1, m),
                                 (MAGIC + 2, m),
                                 (MAGIC + 3, m),
                                 (MAGIC + 4, m)])

        self.randomizeAll()
        self.doSim(500 * Time.ns)

        self.assertValSequenceEqual(u.decoded.field0._ag.dout,
                                    [MAGIC,
                                     MAGIC + 2
                                     ])
        self.assertValSequenceEqual(u.decoded.field1._ag.dout,
                                    [MAGIC + 1,
                                     MAGIC + 3
                                     ])
        self.assertValSequenceEqual(u.bus.b._ag.data, [RESP_OKAY for _ in range(4)] + [RESP_SLVERR])

    def test_registerMap(self):
        self.mySetUp(32)
        s = AddressSpaceProbe.pprint(self.registerMap, doPrint=False)
        expected = \
"""0x%x:field0
0x%x:field1""" % tuple(self.FIELD_ADDR)
        self.assertEqual(s, expected)


class AxiLiteEndpointDenseTC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x8]


class AxiLiteEndpointDenseStartTC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x4, 0x8]


class AxiLiteEndpointOffsetTC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structTwoFields
    FIELD_ADDR = [0x4, 0x8]

    def mySetUp(self, data_width=32):
        u = self.u = AxiLiteEndpoint(self.STRUCT_TEMPLATE, offset=0x4 * 8)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u


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
            regs.field0.read(i)
            regs.field1.read(i)

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
            regs.field0.write(i, MAGIC + i + 1)
            regs.field1.write(i, 2 * MAGIC + i + 1)

        self.randomizeAll()
        self.doSim(2 * 8 * 100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        for i in range(4):
            self.assertValEqual(u.decoded.field0._ag.mem[i], MAGIC + i + 1, "index=%d" % i)
            self.assertValEqual(u.decoded.field1._ag.mem[i], 2 * MAGIC + i + 1, "index=%d" % i)

    def test_registerMap(self):
        self.mySetUp(32)
        s = AddressSpaceProbe.pprint(self.registerMap, doPrint=False)
        expected = \
"""0x%x:field0(size=4)
0x%x:field1(size=4)""" % tuple(self.FIELD_ADDR)
        self.assertEqual(s, expected)


class AxiLiteEndpointStructsInArray(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structStructsInArray
    
    def mySetUp(self, data_width=32):
        u = self.u = AxiLiteEndpoint(self.STRUCT_TEMPLATE, shouldEnterFn=lambda tmpl: True)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    suite.addTest(AxiLiteEndpointStructsInArray('test_nop'))
    # suite.addTest(unittest.makeSuite(AxiLiteEndpointTC))
    # suite.addTest(unittest.makeSuite(AxiLiteEndpointDenseStartTC))
    # suite.addTest(unittest.makeSuite(AxiLiteEndpointDenseTC))
    # suite.addTest(unittest.makeSuite(AxiLiteEndpointOffsetTC))
    # suite.addTest(unittest.makeSuite(AxiLiteEndpointArray))
    #suite.addTest(unittest.makeSuite(AxiLiteEndpointStructsInArray))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
