#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import READ, WRITE
from hwt.interfaces.std import BramPort_withoutClk
from hwt.simulator.simTestCase import SimTestCase

from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.endpoint_test import structTwoFields, \
    structTwoFieldsDense, structTwoFieldsDenseStart, structTwoFieldsDense_str, \
    structTwoFields_str, structTwoFieldsDenseStart_str, \
    AxiLiteEndpointMemMasterTC
from hwtLib.avalon.endpoint import AvalonMmEndpoint
from hwtLib.avalon.memSpaceMaster import AvalonMmMemSpaceMaster
from hwtLib.avalon.mm import AvalonMM, RESP_OKAY, RESP_SLAVEERROR
from pycocotb.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


def addrGetter(intf):
    if isinstance(intf, AvalonMM):
        return intf.address
    elif isinstance(intf, BramPort_withoutClk):
        return intf.addr
    else:
        raise TypeError(intf)


class AvalonMmEndpointTC(SimTestCase):
    STRUCT_TEMPLATE = structTwoFields
    FIELD_ADDR = [0x0, 0x4]
    CLK = CLK_PERIOD

    def arTrans(self, addr, burstsize=1):
        return (READ, addr, burstsize)

    def awTrans(self, addr, burstsize=1):
        return (WRITE, addr, burstsize)

    def mkRegisterMap(self, u):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = AvalonMmMemSpaceMaster(u.bus, self.addrProbe.discovered)

    def randomizeAll(self):
        u = self.u
        for intf in u._interfaces:
            if (intf not in (u.clk, u.rst_n, u.bus)
                    and not isinstance(intf, BramPort_withoutClk)):
                self.randomize(intf)

        self.randomize(u.bus)

    def mySetUp(self, data_width=32, structT=None):
        if structT is None:
            structT = self.STRUCT_TEMPLATE
        u = self.u = AvalonMmEndpoint(structT)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(10 * self.CLK)

        self.assertEmpty(u.bus._ag.rData)
        self.assertEmpty(u.bus._ag.wResp)
        self.assertEmpty(u.decoded.field0._ag.dout)
        self.assertEmpty(u.decoded.field1._ag.dout)

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR

        u.bus._ag.req.extend(
            map(self.arTrans,
                [A[0], A[1], A[0], A[1], A[1] + 0x4]))

        u.decoded.field0._ag.din.extend([MAGIC])
        u.decoded.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.runSim(30 * self.CLK)

        self.assertValSequenceEqual(u.bus._ag.rData,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (None, RESP_SLAVEERROR)])

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        m = mask(32 // 8)
        A = self.FIELD_ADDR
        u.bus._ag.req.extend(
            map(self.awTrans,
                [A[0],
                 A[1],
                 A[0],
                 A[1],
                 A[1] + 0x4]))
        u.bus._ag.wData.extend(
            [(MAGIC, m),
             (MAGIC + 1, m),
             (MAGIC + 2, m),
             (MAGIC + 3, m),
             (MAGIC + 4, m)])

        self.randomizeAll()
        self.runSim(50 * self.CLK)

        self.assertValSequenceEqual(
            u.decoded.field0._ag.dout,
            [MAGIC,
             MAGIC + 2
             ])
        self.assertValSequenceEqual(
            u.decoded.field1._ag.dout,
            [MAGIC + 1,
             MAGIC + 3
             ])
        self.assertValSequenceEqual(
            u.bus._ag.wResp,
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
        u = AvalonMmEndpointTC.mySetUp(self, 32, structT)
        MAGIC = 100

        regs = self.regs
        regs.field0.read()
        regs.field1.read()
        regs.field0.read()
        regs.field1.read()

        u.decoded.field0._ag.din.extend([MAGIC])
        u.decoded.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.runSim(30 * self.CLK)

        self.assertValSequenceEqual(u.bus._ag.rData,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY)])

    def _test_write_memMaster(self, structT):
        u = AvalonMmEndpointTC.mySetUp(self, 32, structT)
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
            u.decoded.field0._ag.dout,
            [MAGIC,
             MAGIC + 2
             ])
        self.assertValSequenceEqual(
            u.decoded.field1._ag.dout,
            [MAGIC + 1,
             MAGIC + 3
             ])
        self.assertValSequenceEqual(
            u.bus._ag.wResp,
            [RESP_OKAY for _ in range(4)])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AvalonMmEndpointTC('test_write'))
    suite.addTest(unittest.makeSuite(AvalonMmEndpointTC))
    suite.addTest(unittest.makeSuite(AvalonMmEndpointDenseStartTC))
    suite.addTest(unittest.makeSuite(AvalonMmEndpointDenseTC))
    suite.addTest(unittest.makeSuite(AvalonMmMemMasterTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
