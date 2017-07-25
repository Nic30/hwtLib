from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.std import BramPort_withoutClk
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite import AxiLite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.constants import RESP_OKAY, RESP_SLVERR
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster
from hwtLib.types.ctypes import uint32_t


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

    def mkRegisterMap(self, u, modelCls):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(u.bus, self.addrProbe.discovered)

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
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        expected = """struct {
    <Bits, 32bits, unsigned> field0 // start:0x0(bit) 0x0(byte)
    <Bits, 32bits, unsigned> field1 // start:0x20(bit) 0x4(byte)
}"""
        self.assertEqual(s, expected)


class AxiLiteEndpointDenseTC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x8]

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        expected = """struct {
    <Bits, 32bits, unsigned> field0 // start:0x0(bit) 0x0(byte)
    //<Bits, 32bits, unsigned> empty space // start:0x20(bit) 0x4(byte)
    <Bits, 32bits, unsigned> field1 // start:0x40(bit) 0x8(byte)
}"""
        self.assertEqual(s, expected)


class AxiLiteEndpointDenseStartTC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x4, 0x8]

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        expected = """struct {
    //<Bits, 32bits, unsigned> empty space // start:0x0(bit) 0x0(byte)
    <Bits, 32bits, unsigned> field0 // start:0x20(bit) 0x4(byte)
    <Bits, 32bits, unsigned> field1 // start:0x40(bit) 0x8(byte)
}"""
        self.assertEqual(s, expected)

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AxiLiteEndpointStructsInArray('test_write'))
    suite.addTest(unittest.makeSuite(AxiLiteEndpointTC))
    suite.addTest(unittest.makeSuite(AxiLiteEndpointDenseStartTC))
    suite.addTest(unittest.makeSuite(AxiLiteEndpointDenseTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    # u = AxiLiteEndpoint(structStructsInArray, shouldEnterFn=lambda tmpl: True)
    # u.DATA_WIDTH.set(32)
    # print(toRtl(u))
