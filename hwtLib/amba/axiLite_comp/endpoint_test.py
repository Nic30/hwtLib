#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.std import HwIOBramPort_noClk
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axiLite_comp.sim.memSpaceMaster import AxiLiteMemSpaceMaster
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.constants import RESP_OKAY, RESP_SLVERR
from hwtLib.types.ctypes import uint32_t
from pyMathBitPrecise.bit_utils import mask

structTwoFields = HStruct(
    (uint32_t, "field0"),
    (uint32_t, "field1")
)

structTwoFields_str = """\
struct {
    <HBits, 32bits, unsigned> field0 // start:0x0(bit) 0x0(byte)
    <HBits, 32bits, unsigned> field1 // start:0x20(bit) 0x4(byte)
}"""

structTwoFieldsDense = HStruct(
    (uint32_t, "field0"),
    (uint32_t, None),
    (uint32_t, "field1")
)

structTwoFieldsDense_str = """\
struct {
    <HBits, 32bits, unsigned> field0 // start:0x0(bit) 0x0(byte)
    //<HBits, 32bits, unsigned> empty space // start:0x20(bit) 0x4(byte)
    <HBits, 32bits, unsigned> field1 // start:0x40(bit) 0x8(byte)
}"""

structTwoFieldsDenseStart = HStruct(
    (uint32_t, None),
    (uint32_t, "field0"),
    (uint32_t, "field1")
)

structTwoFieldsDenseStart_str = """\
struct {
    //<HBits, 32bits, unsigned> empty space // start:0x0(bit) 0x0(byte)
    <HBits, 32bits, unsigned> field0 // start:0x20(bit) 0x4(byte)
    <HBits, 32bits, unsigned> field1 // start:0x40(bit) 0x8(byte)
}"""


def addrGetter(hwIO):
    if isinstance(hwIO, Axi4Lite):
        return hwIO.ar.addr
    elif isinstance(hwIO, HwIOBramPort_noClk):
        return hwIO.addr
    else:
        raise TypeError(hwIO)


class AxiLiteEndpointTC(SimTestCase):
    STRUCT_TEMPLATE = structTwoFields
    FIELD_ADDR = [0x0, 0x4]
    CLK = 10 * Time.ns

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def mkRegisterMap(self, u):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(u.bus, self.addrProbe.discovered)

    def randomizeAll(self):
        dut = self.dut
        for hwIO in dut._hwIOs:
            if (hwIO not in (dut.clk, dut.rst_n, dut.bus)
                    and not isinstance(hwIO, HwIOBramPort_noClk)):
                self.randomize(hwIO)
        axi_randomize_per_channel(self, dut.bus)

    def mySetUp(self, data_width=32, STRUCT_TEMPLATE=None):
        if STRUCT_TEMPLATE is None:
            STRUCT_TEMPLATE = self.STRUCT_TEMPLATE
        dut = self.dut = AxiLiteEndpoint(STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        dut.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.dut, onAfterToRtl=self.mkRegisterMap)
        return dut

    def test_nop(self):
        dut = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(10 * self.CLK)

        self.assertEmpty(dut.bus._ag.r.data)
        self.assertEmpty(dut.decoded.field0._ag.dout)
        self.assertEmpty(dut.decoded.field1._ag.dout)

    def test_read(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR

        a = dut.bus.ar._ag.create_addr_req
        dut.bus.ar._ag.data.extend(map(a,
                                     [A[0], A[1], A[0], A[1], A[1] + 0x4]))

        dut.decoded.field0._ag.din.extend([MAGIC])
        dut.decoded.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.runSim(30 * self.CLK)

        self.assertValSequenceEqual(dut.bus.r._ag.data,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (None, RESP_SLVERR)])

    def test_write(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        m = mask(32 // 8)
        A = self.FIELD_ADDR

        a = dut.bus.ar._ag.create_addr_req
        dut.bus.aw._ag.data.extend(map(a,
                                     [A[0],
                                      A[1],
                                      A[0],
                                      A[1],
                                      A[1] + 0x4]))
        dut.bus.w._ag.data.extend([(MAGIC, m),
                                 (MAGIC + 1, m),
                                 (MAGIC + 2, m),
                                 (MAGIC + 3, m),
                                 (MAGIC + 4, m)])

        self.randomizeAll()
        self.runSim(50 * self.CLK)

        self.assertValSequenceEqual(dut.decoded.field0._ag.dout,
                                    [MAGIC,
                                     MAGIC + 2
                                     ])
        self.assertValSequenceEqual(dut.decoded.field1._ag.dout,
                                    [MAGIC + 1,
                                     MAGIC + 3
                                     ])
        self.assertValSequenceEqual(
            dut.bus.b._ag.data, [RESP_OKAY for _ in range(4)] + [RESP_SLVERR])

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, structTwoFields_str)


class AxiLiteEndpointDenseTC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x8]

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, structTwoFieldsDense_str)


class AxiLiteEndpointDenseStartTC(AxiLiteEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x4, 0x8]

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, structTwoFieldsDenseStart_str)


class AxiLiteEndpointMemMasterTC(SimTestCase):
    CLK = AxiLiteEndpointTC.CLK

    def randomizeAll(self):
        AxiLiteEndpointTC.randomizeAll(self)

    def mkRegisterMap(self, u):
        AxiLiteEndpointTC.mkRegisterMap(self, u)

    def _test_read_memMaster(self, structT):
        dut = AxiLiteEndpointTC.mySetUp(self, 32, structT)
        MAGIC = 100

        regs = self.regs
        regs.field0.read()
        regs.field1.read()
        regs.field0.read()
        regs.field1.read()

        dut.decoded.field0._ag.din.extend([MAGIC])
        dut.decoded.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.runSim(30 * self.CLK)

        self.assertValSequenceEqual(dut.bus.r._ag.data,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY)
                                     ])

    def _test_write_memMaster(self, structT):
        dut = AxiLiteEndpointTC.mySetUp(self, 32, structT)
        MAGIC = 100
        regs = self.regs
        f0, f1 = regs.field0, regs.field1
        f0.write(MAGIC)
        f1.write(MAGIC + 1)
        f0.write(MAGIC + 2)
        f1.write(MAGIC + 3)

        self.randomizeAll()
        self.runSim(50 * self.CLK)

        self.assertValSequenceEqual(dut.decoded.field0._ag.dout,
                                    [MAGIC,
                                     MAGIC + 2
                                     ])
        self.assertValSequenceEqual(dut.decoded.field1._ag.dout,
                                    [MAGIC + 1,
                                     MAGIC + 3
                                     ])
        self.assertValSequenceEqual(
            dut.bus.b._ag.data, [RESP_OKAY for _ in range(4)])

    def test_read_memMaster(self):
        self._test_read_memMaster(structTwoFields)

    def test_write_memMaster(self):
        self._test_write_memMaster(structTwoFields)

    def test_read_holeBefore_memMaster(self):
        self._test_read_memMaster(structTwoFieldsDenseStart)

    def test_write_holeBefore_memMaster(self):
        self._test_write_memMaster(structTwoFieldsDenseStart)

    def test_read_holeInside_memMaster(self):
        self._test_read_memMaster(structTwoFieldsDense)

    def test_write_holeInside_memMaster(self):
        self._test_write_memMaster(structTwoFieldsDense)


AxiLiteEndpointTCs = [
    AxiLiteEndpointTC,
    AxiLiteEndpointDenseStartTC,
    AxiLiteEndpointDenseTC,
    AxiLiteEndpointMemMasterTC
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiLiteEndpointStructsInArray("test_write")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in AxiLiteEndpointTCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    # m = AxiLiteEndpoint(structStructsInArray,
    #                     shouldEnterFn=lambda tmpl: True)
    # m.DATA_WIDTH = 32
    # print(to_rtl_str(m))
