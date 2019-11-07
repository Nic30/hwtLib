#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time, READ, WRITE, NOP
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC, \
    addrGetter, structTwoFieldsDense, \
    structTwoFieldsDenseStart, AxiLiteEndpointDenseStartTC, \
    AxiLiteEndpointDenseTC
from hwtLib.mem.bramPortEndpoint import BramPortEndpoint
from hwtLib.mem.bramPortSimMemSpaceMaster import BramPortSimMemSpaceMaster
from hwtLib.amba.axiLite_comp.endpoint_arr_test import AxiLiteEndpointArrayTC


class BramPortEndpointTC(AxiLiteEndpointTC):
    FIELD_ADDR = [0x0, 0x1]

    def mkRegisterMap(self, u):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = BramPortSimMemSpaceMaster(u.bus, self.addrProbe.discovered)

    def mySetUp(self, data_width=32):
        u = self.u = BramPortEndpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def randomizeAll(self):
        pass

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.readed)
        self.assertFalse(u.bus._ag.readPending)
        self.assertEmpty(u.decoded.field0._ag.dout)
        self.assertEmpty(u.decoded.field1._ag.dout)

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR
        u.bus._ag.requests.extend([(READ, A[0]),
                                   (READ, A[1]),
                                   (READ, A[0]),
                                   (READ, A[1])
                                   ])

        u.decoded.field0._ag.din.append(MAGIC)
        u.decoded.field1._ag.din.append(MAGIC + 1)

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertValSequenceEqual(u.bus._ag.readed, [MAGIC,
                                                       MAGIC + 1,
                                                       MAGIC,
                                                       MAGIC + 1])

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR
        u.bus._ag.requests.extend([
            NOP,  # assert is after reset
            (WRITE, A[0], MAGIC),
            (WRITE, A[1], MAGIC + 1),
            (WRITE, A[0], MAGIC + 2),
            (WRITE, A[1], MAGIC + 3)])

        self.randomizeAll()
        self.runSim(400 * Time.ns)

        self.assertValSequenceEqual(u.decoded.field0._ag.dout,
                                    [MAGIC,
                                     MAGIC + 2],
                                    "field0")
        self.assertValSequenceEqual(u.decoded.field1._ag.dout,
                                    [MAGIC + 1,
                                     MAGIC + 3],
                                    "field1")


class BramPortEndpointDenseTC(BramPortEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x2]

    def test_registerMap(self):
        AxiLiteEndpointDenseTC.test_registerMap(self)


class BramPortEndpointDenseStartTC(BramPortEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x1, 0x2]

    def test_registerMap(self):
        AxiLiteEndpointDenseStartTC.test_registerMap(self)


class BramPortEndpointArrayTC(AxiLiteEndpointArrayTC):
    FIELD_ADDR = [0x0, 0x4]
    mkRegisterMap = BramPortEndpointTC.mkRegisterMap
    mySetUp = BramPortEndpointTC.mySetUp

    def randomizeAll(self):
        pass

    def test_nop(self):
        u = self.mySetUp(32)
        MAGIC = 100

        for i in range(8):
            u.decoded.field0._ag.mem[i] = MAGIC + 1 + i
            u.decoded.field1._ag.mem[i] = 2 * MAGIC + 1 + i

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.readed)
        for i in range(8):
            self.assertValEqual(u.decoded.field0._ag.mem[i], MAGIC + 1 + i)
            self.assertValEqual(u.decoded.field1._ag.mem[i], 2 * MAGIC + 1 + i)

    def test_read(self):
        u = self.mySetUp(32)
        # u.bus._ag._debug(sys.stdout)
        regs = self.regs
        MAGIC = 100
        # u.bus._ag.requests.append(NOP)
        for i in range(4):
            u.decoded.field0._ag.mem[i] = MAGIC + i + 1
            u.decoded.field1._ag.mem[i] = 2 * MAGIC + i + 1
            regs.field0[i].read()
            regs.field1[i].read()

        self.randomizeAll()
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(u.bus._ag.readed,
                                    [MAGIC + 1,
                                     2 * MAGIC + 1,
                                     MAGIC + 2,
                                     2 * MAGIC + 2,
                                     MAGIC + 3,
                                     2 * MAGIC + 3,
                                     MAGIC + 4,
                                     2 * MAGIC + 4,
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
        self.runSim(200 * Time.ns)

        self.assertEmpty(u.bus._ag.readed)
        for i in range(4):
            self.assertValEqual(u.decoded.field0._ag.mem[i], MAGIC + i + 1)
            self.assertValEqual(u.decoded.field1._ag.mem[i], 2 * MAGIC + i + 1)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    #suite.addTest(BramPortEndpointTC('test_read'))
    suite.addTest(unittest.makeSuite(BramPortEndpointTC))
    suite.addTest(unittest.makeSuite(BramPortEndpointDenseTC))
    suite.addTest(unittest.makeSuite(BramPortEndpointDenseStartTC))
    suite.addTest(unittest.makeSuite(BramPortEndpointArrayTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
