#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time, READ, WRITE, NOP
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.structEndpoint_test import AxiLiteStructEndpointTC, \
    addrGetter, AxiLiteStructEndpointArray, structTwoFieldsDense,\
    structTwoFieldsDenseStart
from hwtLib.mem.bramPortSimMemSpaceMaster import BramPortSimMemSpaceMaster
from hwtLib.mem.bramStructEndpoint import BramPortStructEndpoint
import sys


class BramPortStructEndpointTC(AxiLiteStructEndpointTC):
    FIELD_ADDR = [0x0, 0x1]

    def mkRegisterMap(self, u):
        registerMap = AddressSpaceProbe(u.bus, addrGetter).discover()
        self.registerMap = registerMap
        self.regs = BramPortSimMemSpaceMaster(u.bus, registerMap)

    def mySetUp(self, data_width=32):
        u = self.u = BramPortStructEndpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def randomizeAll(self):
        pass

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.doSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.readed)
        self.assertFalse(u.bus._ag.readPending)
        self.assertEmpty(u.field0._ag.dout)
        self.assertEmpty(u.field1._ag.dout)

    def test_read(self):
        u = self.mySetUp( 32)
        MAGIC = 100
        A = self.FIELD_ADDR
        u.bus._ag.requests.extend([(READ, A[0]),
                                   (READ, A[1]),
                                   (READ, A[0]),
                                   (READ, A[1])
                                   ])

        u.field0._ag.din.append(MAGIC)
        u.field1._ag.din.append(MAGIC + 1)

        self.randomizeAll()
        self.doSim(300 * Time.ns)

        self.assertValSequenceEqual(u.bus._ag.readed, [MAGIC,
                                                       MAGIC + 1,
                                                       MAGIC,
                                                       MAGIC + 1])

    def test_write(self):
        u = self.mySetUp( 32)
        MAGIC = 100
        A = self.FIELD_ADDR
        u.bus._ag.requests.extend([
            NOP, # assert is after reset
            (WRITE, A[0], MAGIC),
            (WRITE, A[1], MAGIC + 1),
            (WRITE, A[0], MAGIC + 2),
            (WRITE, A[1], MAGIC + 3)])

        self.randomizeAll()
        self.doSim(400 * Time.ns)

        self.assertValSequenceEqual(u.field0._ag.dout, [MAGIC,
                                                        MAGIC + 2
                                                        ])
        self.assertValSequenceEqual(u.field1._ag.dout, [MAGIC + 1,
                                                        MAGIC + 3
                                                        ])


class BramPortStructEndpointDenseTC(BramPortStructEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x2]
    

class BramPortStructEndpointStartTC(BramPortStructEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x1, 0x2]


class BramPortStructEndpointOffsetTC(BramPortStructEndpointTC):
    FIELD_ADDR = [0x1, 0x2]

    def mySetUp(self, data_width=32):
        u = self.u = BramPortStructEndpoint(self.STRUCT_TEMPLATE, offset=0x1)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

class BramPortStructEndpointArray(AxiLiteStructEndpointArray):
    FIELD_ADDR = [0x0, 0x4]
    mkRegisterMap = BramPortStructEndpointTC.mkRegisterMap
    mySetUp = BramPortStructEndpointTC.mySetUp

    def randomizeAll(self):
        pass


    def test_nop(self):
        u = self.mySetUp(32)
        MAGIC = 100

        for i in range(8):
            u.field0._ag.mem[i] = MAGIC + 1 + i
            u.field1._ag.mem[i] = 2 * MAGIC + 1 + i

        self.randomizeAll()
        self.doSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.readed)
        for i in range(8):
            self.assertValEqual(u.field0._ag.mem[i], MAGIC + 1 + i)
            self.assertValEqual(u.field1._ag.mem[i], 2 * MAGIC + 1 + i)

    def test_read(self):
        u = self.mySetUp(32)
        #u.bus._ag._debug(sys.stdout)
        regs = self.regs
        MAGIC = 100
        #u.bus._ag.requests.append(NOP)
        for i in range(4):
            u.field0._ag.mem[i] = MAGIC + i + 1
            u.field1._ag.mem[i] = 2 * MAGIC + i + 1
            regs.field0.read(i, None)
            regs.field1.read(i, None)

        self.randomizeAll()
        self.doSim(200 * Time.ns)

        self.assertValSequenceEqual(u.bus._ag.readed, [
            MAGIC + 1,
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
            u.field0._ag.mem[i] = None
            u.field1._ag.mem[i] = None
            regs.field0.write(i, MAGIC + i + 1)
            regs.field1.write(i, 2 * MAGIC + i + 1)

        self.randomizeAll()
        self.doSim(200 * Time.ns)

        self.assertEmpty(u.bus._ag.readed)
        for i in range(4):
            self.assertValEqual(u.field0._ag.mem[i], MAGIC + i + 1)
            self.assertValEqual(u.field1._ag.mem[i], 2 * MAGIC + i + 1)






if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    #suite.addTest(BramPortStructEndpointArray('test_read'))
    suite.addTest(unittest.makeSuite(BramPortStructEndpointTC))
    suite.addTest(unittest.makeSuite(BramPortStructEndpointDenseTC))
    suite.addTest(unittest.makeSuite(BramPortStructEndpointStartTC))
    suite.addTest(unittest.makeSuite(BramPortStructEndpointOffsetTC))
    suite.addTest(unittest.makeSuite(BramPortStructEndpointArray))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
