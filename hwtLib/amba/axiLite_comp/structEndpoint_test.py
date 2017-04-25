from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.struct import HStruct
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.structEndpoint import AxiLiteStructEndpoint
from hwtLib.amba.constants import RESP_OKAY
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


def addrGetter(intf):
    if isinstance(intf, AxiLite):
        return intf.ar.addr
    elif isinstance(intf, BramPort_withoutClk):
        return intf.addr
    else:
        raise TypeError(intf)


class AxiLiteStructEndpointTC(SimTestCase):
    STRUCT_TEMPLATE = structTwoFields
    FIELD_ADDR = [0x0, 0x4]

    def mkRegisterMap(self, u):
        registerMap = AddressSpaceProbe(u.bus, addrGetter).discover()
        self.registerMap = registerMap
        self.regs = AxiLiteMemSpaceMaster(u.bus, registerMap)

    def randomizeAll(self):
        u = self.u
        for intf in u._interfaces:
            if u not in (u.clk, u.rst_n, u.bus):
                self.randomize(intf)

        self.randomize(u.bus.ar)
        self.randomize(u.bus.aw)
        self.randomize(u.bus.r)
        self.randomize(u.bus.w)
        self.randomize(u.bus.b)

    def mySetUp(self, structTmpl, data_width=32):
        u = self.u = AxiLiteStructEndpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(structTwoFields, 32)

        self.randomizeAll()
        self.doSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        self.assertEmpty(u.field0._ag.dout)
        self.assertEmpty(u.field1._ag.dout)

    def test_simpleRead(self):
        u = self.mySetUp(structTwoFields, 32)
        MAGIC = 100
        A = self.FIELD_ADDR
        u.bus.ar._ag.data.extend([A[0], A[1], A[0], A[1], A[1] + 0x4])

        u.field0._ag.din.extend([MAGIC])
        u.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.doSim(300 * Time.ns)

        self.assertValSequenceEqual(u.bus.r._ag.data, [(MAGIC, RESP_OKAY),
                                                       (MAGIC + 1, RESP_OKAY),
                                                       (MAGIC, RESP_OKAY),
                                                       (MAGIC + 1, RESP_OKAY)])

    def test_simpleWrite(self):
        u = self.mySetUp(structTwoFields, 32)
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
        self.doSim(400 * Time.ns)

        self.assertValSequenceEqual(u.field0._ag.dout, [MAGIC,
                                                        MAGIC + 2
                                                        ])
        self.assertValSequenceEqual(u.field1._ag.dout, [MAGIC + 1,
                                                        MAGIC + 3
                                                        ])
        self.assertValSequenceEqual(u.bus.w._ag.actualData, (MAGIC + 4, m))
        self.assertValSequenceEqual(u.bus.b._ag.data, [RESP_OKAY for _ in range(4)])

    def test_registerMap(self):
        u = self.mySetUp(structTwoFields, 32)
        s = AddressSpaceProbe.pprint(self.registerMap, doPrint=False)
        expected = \
"""0x0:field0
0x4:field1"""
        self.assertEqual(s, expected)

class AxiLiteStructEndpointDenseTC(AxiLiteStructEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x8]
    
    def test_registerMap(self):
        u = self.mySetUp(structTwoFields, 32)
        s = AddressSpaceProbe.pprint(self.registerMap, doPrint=False)
        expected = \
"""0x0:field0
0x8:field1"""
        self.assertEqual(s, expected)


class AxiLiteStructEndpointDenseStartTC(AxiLiteStructEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x4, 0x8]

    def test_registerMap(self):
        u = self.mySetUp(structTwoFields, 32)
        s = AddressSpaceProbe.pprint(self.registerMap, doPrint=False)
        expected = \
"""0x4:field0
0x8:field1"""
        self.assertEqual(s, expected)


class AxiLiteStructEndpointOffsetTC(AxiLiteStructEndpointTC):
    STRUCT_TEMPLATE = structTwoFields
    FIELD_ADDR = [0x4, 0x8]

    def mySetUp(self, structTmpl, data_width=32):
        u = self.u = AxiLiteStructEndpoint(self.STRUCT_TEMPLATE, offset=0x4)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_registerMap(self):
        u = self.mySetUp(structTwoFields, 32)
        s = AddressSpaceProbe.pprint(self.registerMap, doPrint=False)
        expected = \
"""0x4:field0
0x8:field1"""
        self.assertEqual(s, expected)


class AxiLiteStructEndpointArray(SimTestCase):
    STRUCT_TEMPLATE = structTwoArr
    FIELD_ADDR = [0x4, 0x8]
    mkRegisterMap = AxiLiteStructEndpointTC.mkRegisterMap
    mySetUp = AxiLiteStructEndpointTC.mySetUp

    def randomizeAll(self):
        u = self.u

        self.randomize(u.bus.ar)
        self.randomize(u.bus.aw)
        self.randomize(u.bus.r)
        self.randomize(u.bus.w)
        self.randomize(u.bus.b)

    def test_nop(self):
        u = self.mySetUp(structTwoFields, 32)
        MAGIC = 100

        for i in range(8):
            u.field0._ag.mem[i] = MAGIC + 1
            u.field1._ag.mem[i] = 2 * MAGIC + 1

        self.randomizeAll()
        self.doSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        for i in range(8):
            self.assertValEqual(u.field0._ag.mem[i], MAGIC + 1)
            self.assertValEqual(u.field1._ag.mem[i], 2 * MAGIC + 1)

    def test_write(self):
        u = self.mySetUp(structTwoFields, 32)
        regs = self.regs
        MAGIC = 100

        for i in range(4):
            u.field0._ag.mem[i] = None
            u.field1._ag.mem[i] = None
            regs.field0.write(i, MAGIC + i + 1)
            regs.field1.write(i, 2 * MAGIC + i + 1)

        self.randomizeAll()
        self.doSim(2 * 8 * 100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        for i in range(4):
            self.assertValEqual(u.field0._ag.mem[i], MAGIC + i + 1)
            self.assertValEqual(u.field1._ag.mem[i], 2 * MAGIC + i + 1)

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    #suite.addTest(Axi4_streamToMemTC('test_endstrbMultiFrame'))
    suite.addTest(unittest.makeSuite(AxiLiteStructEndpointTC))
    suite.addTest(unittest.makeSuite(AxiLiteStructEndpointDenseStartTC))
    suite.addTest(unittest.makeSuite(AxiLiteStructEndpointDenseTC))
    suite.addTest(unittest.makeSuite(AxiLiteStructEndpointOffsetTC))
    suite.addTest(unittest.makeSuite(AxiLiteStructEndpointArray))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
