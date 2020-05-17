#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time, WRITE, NOP
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.endpoint_test import \
    addrGetter as axi_addrGetter, structTwoFieldsDense, \
    structTwoFieldsDenseStart, AxiLiteEndpointDenseStartTC, \
    AxiLiteEndpointDenseTC
from hwtLib.cesnet.mi32.endpoint import Mi32Endpoint
from hwtLib.cesnet.mi32.mi32SimMemSpaceMaster import Mi32SimMemSpaceMaster
from hwtLib.cesnet.mi32.intf import Mi32
from pyMathBitPrecise.bit_utils import mask
from hwtLib.mem.bramEndpoint_test import BramPortEndpointTC,\
    BramPortEndpointArrayTC

# [TODO] very similar to hwtLib.mem.bramEndpoint_test

def addrGetter(intf):
    if isinstance(intf, Mi32):
        return intf.addr
    else:
        return axi_addrGetter(intf)


class Mi32EndpointTC(BramPortEndpointTC):
    FIELD_ADDR = [0x0, 0x4]

    def mkRegisterMap(self, u):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = Mi32SimMemSpaceMaster(u.bus, self.addrProbe.discovered)

    def mySetUp(self, data_width=32):
        u = self.u = Mi32Endpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r_data)
        self.assertEmpty(u.decoded.field0._ag.dout)
        self.assertEmpty(u.decoded.field1._ag.dout)

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR
        m = mask(self.DATA_WIDTH//8)
        u.bus._ag.requests.extend([
            NOP,  # assert is after reset
            (WRITE, A[0], MAGIC, m),
            (WRITE, A[1], MAGIC + 1, m),
            (WRITE, A[0], MAGIC + 2, m),
            (WRITE, A[1], MAGIC + 3, m)])

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


class Mi32EndpointDenseTC(Mi32EndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDense
    FIELD_ADDR = [0x0, 0x8]

    def test_registerMap(self):
        AxiLiteEndpointDenseTC.test_registerMap(self)


class Mi32EndpointDenseStartTC(Mi32EndpointTC):
    STRUCT_TEMPLATE = structTwoFieldsDenseStart
    FIELD_ADDR = [0x4, 0x8]

    def test_registerMap(self):
        AxiLiteEndpointDenseStartTC.test_registerMap(self)


class Mi32EndpointArrayTC(BramPortEndpointArrayTC):
    FIELD_ADDR = [0x0, 0x10]
    mkRegisterMap = Mi32EndpointTC.mkRegisterMap
    mySetUp = Mi32EndpointTC.mySetUp

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

        self.assertEmpty(u.bus._ag.r_data)
        for i in range(4):
            self.assertValEqual(u.decoded.field0._ag.mem[i], MAGIC + i + 1)
            self.assertValEqual(u.decoded.field1._ag.mem[i], 2 * MAGIC + i + 1)


Mi32EndpointTCs = [
    Mi32EndpointTC,
    Mi32EndpointDenseTC,
    Mi32EndpointArrayTC,
    Mi32EndpointDenseStartTC
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(Mi32EndpointTC('test_read'))
    for tc in Mi32EndpointTCs:
        suite.addTest(unittest.makeSuite(tc))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
