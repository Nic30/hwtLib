#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time, READ, WRITE, NOP
from hwt.hwIOs.std import HwIOBramPort_noClk
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.endpoint_arr_test import AxiLiteEndpointArrayTC
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC, \
    structTwoFieldsDense, structTwoFieldsDenseStart, AxiLiteEndpointDenseTC, \
    AxiLiteEndpointDenseStartTC
from hwtLib.xilinx.ipif.endpoint import IpifEndpoint
from hwtLib.xilinx.ipif.hIOIpif import Ipif
from hwtLib.xilinx.ipif.simMaster import IPFISimMaster
from pyMathBitPrecise.bit_utils import mask


def addrGetter(hwIO):
    if isinstance(hwIO, Ipif):
        return hwIO.bus2ip_addr
    elif isinstance(hwIO, HwIOBramPort_noClk):
        return hwIO.addr
    else:
        raise TypeError(hwIO)


class IpifEndpointTC(AxiLiteEndpointTC):
    FIELD_ADDR = [0x0, 0x4]

    def mkRegisterMap(self, u):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = IPFISimMaster(u.bus, self.addrProbe.discovered)

    def mySetUp(self, data_width=32):
        dut = self.dut = IpifEndpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        dut.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.dut, onAfterToRtl=self.mkRegisterMap)
        return dut

    def randomizeAll(self):
        pass

    def test_nop(self):
        dut = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(dut.bus._ag.r_data)
        self.assertIs(dut.bus._ag.actual, NOP)
        self.assertEmpty(dut.decoded.field0._ag.dout)
        self.assertEmpty(dut.decoded.field1._ag.dout)

    def test_read(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR
        dut.bus._ag.requests.extend([(READ, A[0]),
                                   (READ, A[1]),
                                   (READ, A[0]),
                                   (READ, A[1])
                                   ])

        dut.decoded.field0._ag.din.append(MAGIC)
        dut.decoded.field1._ag.din.append(MAGIC + 1)

        self.randomizeAll()
        self.runSim(300 * Time.ns)

        self.assertValSequenceEqual(dut.bus._ag.r_data, [MAGIC,
                                                       MAGIC + 1,
                                                       MAGIC,
                                                       MAGIC + 1])

    def test_write(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR
        m = mask(32 // 8)
        dut.bus._ag.requests.extend([
            (WRITE, A[0], MAGIC, m),
            (WRITE, A[1], MAGIC + 1, m),
            (WRITE, A[0], MAGIC + 2, m),
            (WRITE, A[1], MAGIC + 3, m)])

        self.randomizeAll()
        self.runSim(400 * Time.ns)

        self.assertValSequenceEqual(dut.decoded.field0._ag.dout, [MAGIC,
                                                                MAGIC + 2
                                                                ])
        self.assertValSequenceEqual(dut.decoded.field1._ag.dout, [MAGIC + 1,
                                                                MAGIC + 3
                                                                ])


class IpifEndpointDenseTC(IpifEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x8]

    def test_registerMap(self):
        AxiLiteEndpointDenseTC.test_registerMap(self)


class IpifEndpointDenseStartTC(IpifEndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x4, 0x8]

    def test_registerMap(self):
        AxiLiteEndpointDenseStartTC.test_registerMap(self)


class IpifEndpointArray(AxiLiteEndpointArrayTC):
    FIELD_ADDR = [0x0, 0x10]
    mkRegisterMap = IpifEndpointTC.mkRegisterMap
    mySetUp = IpifEndpointTC.mySetUp

    def randomizeAll(self):
        pass

    def test_nop(self):
        dut = self.mySetUp(32)
        MAGIC = 100

        for i in range(8):
            dut.decoded.field0._ag.mem[i] = MAGIC + 1 + i
            dut.decoded.field1._ag.mem[i] = 2 * MAGIC + 1 + i

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(dut.bus._ag.r_data)
        for i in range(8):
            self.assertValEqual(dut.decoded.field0._ag.mem[i], MAGIC + 1 + i)
            self.assertValEqual(dut.decoded.field1._ag.mem[i], 2 * MAGIC + 1 + i)

    def test_read(self):
        dut = self.mySetUp(32)
        # dut.bus._ag._debug(sys.stdout)
        regs = self.regs
        MAGIC = 100
        # dut.bus._ag.requests.append(NOP)
        for i in range(4):
            dut.decoded.field0._ag.mem[i] = MAGIC + i + 1
            dut.decoded.field1._ag.mem[i] = 2 * MAGIC + i + 1
            regs.field0[i].read()
            regs.field1[i].read()

        self.randomizeAll()
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(dut.bus._ag.r_data,
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
        dut = self.mySetUp(32)
        regs = self.regs
        MAGIC = 100

        for i in range(4):
            dut.decoded.field0._ag.mem[i] = None
            dut.decoded.field1._ag.mem[i] = None
            regs.field0[i].write(MAGIC + i + 1)
            regs.field1[i].write(2 * MAGIC + i + 1)

        self.randomizeAll()
        self.runSim(400 * Time.ns)

        self.assertEmpty(dut.bus._ag.r_data)
        for i in range(4):
            self.assertValEqual(
                dut.decoded.field0._ag.mem[i], MAGIC + i + 1, f"index={i:d}")
            self.assertValEqual(
                dut.decoded.field1._ag.mem[i], 2 * MAGIC + i + 1, f"index={i:d}")


if __name__ == "__main__":
    import unittest

    _ALL_TCs = [IpifEndpointTC, IpifEndpointDenseTC, IpifEndpointDenseStartTC, IpifEndpointArray]
    testLoader = unittest.TestLoader()
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
