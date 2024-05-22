#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import READ, WRITE
from hwt.hwIOs.std import HwIOBramPort_noClk
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.endpoint_test import structTwoFields, \
    structTwoFieldsDense, structTwoFieldsDenseStart, structTwoFieldsDense_str, \
    structTwoFields_str, structTwoFieldsDenseStart_str, \
    AxiLiteEndpointMemMasterTC
from hwtLib.avalon.endpoint import AvalonMmEndpoint
from hwtLib.avalon.mm import AvalonMM, RESP_OKAY, RESP_SLAVEERROR
from hwtLib.avalon.sim.memSpaceMaster import AvalonMmMemSpaceMaster
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


def addrGetter(hwIO):
    if isinstance(hwIO, AvalonMM):
        return hwIO.address
    elif isinstance(hwIO, HwIOBramPort_noClk):
        return hwIO.addr
    else:
        raise TypeError(hwIO)


class AvalonMmEndpointTC(SimTestCase):
    STRUCT_TEMPLATE = structTwoFields
    FIELD_ADDR = [0x0, 0x4]
    CLK = CLK_PERIOD

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def arTrans(self, addr, burstsize=1):
        return (READ, addr, burstsize, None, None)

    def awTrans(self, addr, data, be, burstsize=1):
        return (WRITE, addr, burstsize, data, be)

    def mkRegisterMap(self, u):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = AvalonMmMemSpaceMaster(u.bus, self.addrProbe.discovered)

    def randomizeAll(self):
        dut = self.dut
        for hwIO in dut._hwIOs:
            if (hwIO not in (dut.clk, dut.rst_n, dut.bus)
                    and not isinstance(hwIO, HwIOBramPort_noClk)):
                self.randomize(hwIO)

        self.randomize(dut.bus)

    def mySetUp(self, data_width=32, structT=None):
        if structT is None:
            structT = self.STRUCT_TEMPLATE
        dut = self.dut = AvalonMmEndpoint(structT)

        self.DATA_WIDTH = data_width
        dut.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.dut, onAfterToRtl=self.mkRegisterMap)
        return dut

    def test_nop(self):
        dut = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(10 * self.CLK)

        self.assertEmpty(dut.bus._ag.rData)
        self.assertEmpty(dut.bus._ag.wResp)
        self.assertEmpty(dut.decoded.field0._ag.dout)
        self.assertEmpty(dut.decoded.field1._ag.dout)

    def test_read(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR

        dut.bus._ag.req.extend(
            map(self.arTrans,
                [A[0], A[1], A[0], A[1], A[1] + 0x4]))

        dut.decoded.field0._ag.din.extend([MAGIC])
        dut.decoded.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.runSim(40 * self.CLK)

        self.assertValSequenceEqual(dut.bus._ag.rData,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (None, RESP_SLAVEERROR)])

    def test_write(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        m = mask(32 // 8)
        A = self.FIELD_ADDR
        dut.bus._ag.req.extend(
            self.awTrans(a, d, m)
            for a, d in [
                (A[0], MAGIC),
                (A[1], MAGIC + 1),
                (A[0], MAGIC + 2),
                (A[1], MAGIC + 3),
                (A[1] + 0x4, MAGIC + 4)
                 ])

        self.randomizeAll()
        self.runSim(50 * self.CLK)

        self.assertValSequenceEqual(
            dut.decoded.field0._ag.dout,
            [MAGIC,
             MAGIC + 2
             ])
        self.assertValSequenceEqual(
            dut.decoded.field1._ag.dout,
            [MAGIC + 1,
             MAGIC + 3
             ])
        self.assertValSequenceEqual(
            dut.bus._ag.wResp,
            [RESP_OKAY for _ in range(4)] + [RESP_SLAVEERROR])

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, structTwoFields_str)


class AvalonMmEndpointDenseTC(AvalonMmEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x8]

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, structTwoFieldsDense_str)


class AvalonMmEndpointDenseStartTC(AvalonMmEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x4, 0x8]

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, structTwoFieldsDenseStart_str)


class AvalonMmMemMasterTC(AxiLiteEndpointMemMasterTC):
    CLK = AvalonMmEndpointTC.CLK

    def randomizeAll(self):
        AvalonMmEndpointTC.randomizeAll(self)

    def mkRegisterMap(self, u):
        AvalonMmEndpointTC.mkRegisterMap(self, u)

    def _test_read_memMaster(self, structT):
        dut = AvalonMmEndpointTC.mySetUp(self, 32, structT)
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

        self.assertValSequenceEqual(dut.bus._ag.rData,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY)])

    def _test_write_memMaster(self, structT):
        dut = AvalonMmEndpointTC.mySetUp(self, 32, structT)
        MAGIC = 100
        regs = self.regs
        f0, f1 = regs.field0, regs.field1
        f0.write(MAGIC)
        f1.write(MAGIC + 1)
        f0.write(MAGIC + 2)
        f1.write(MAGIC + 3)

        self.randomizeAll()
        self.runSim(50 * self.CLK)

        self.assertValSequenceEqual(
            dut.decoded.field0._ag.dout,
            [MAGIC,
             MAGIC + 2
             ])
        self.assertValSequenceEqual(
            dut.decoded.field1._ag.dout,
            [MAGIC + 1,
             MAGIC + 3
             ])
        self.assertValSequenceEqual(
            dut.bus._ag.wResp,
            [RESP_OKAY for _ in range(4)])


AvalonMmEndpointTCs = [
    AvalonMmEndpointTC,
    AvalonMmEndpointDenseStartTC,
    AvalonMmEndpointDenseTC,
    AvalonMmMemMasterTC
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AvalonMmEndpointTC("test_write")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in AvalonMmEndpointTCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
