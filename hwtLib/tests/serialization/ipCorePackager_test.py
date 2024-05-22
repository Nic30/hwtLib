#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import tempfile
import unittest

from hwt.code import If
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.hwIODifferential import HwIODifferentialSig
from hwt.hwIOs.std import HwIOBramPort, HwIODataRdVld
from hwt.hwIOs.std_ip_defs import IP_Handshake
from hwt.hwIOs.utils import addClkRst
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.synth import serializeAsIpcore
from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axi_comp.stream_to_mem import Axi4streamToMem
from hwtLib.amba.axis_comp.en import Axi4S_en
from hwtLib.mem.fifo import Fifo
from hwtLib.peripheral.i2c.masterBitCntrl import I2cMasterBitCtrl
from hwtLib.peripheral.uart.intf import Uart
from hwtLib.types.ctypes import uint64_t


class Handshaked_withIP(HwIODataRdVld):

    @override
    def _getIpCoreIntfClass(self):
        return IP_Handshake


class IpCoreIntfTest(HwModule):

    @override
    def hwDeclr(self):
        addClkRst(self)

        self.ram0 = HwIOBramPort()
        self.ram1 = HwIOBramPort()._m()
        self.uart = Uart()._m()
        self.hsIn = Handshaked_withIP()
        self.hsOut = Handshaked_withIP()._m()
        self.difIn = HwIODifferentialSig()
        self.axi3s0 = Axi3()
        self.axi3m0 = Axi3()._m()

        self.axi3s1 = Axi3()
        self.axi3m1 = Axi3()._m()
        for i in [self.axi3s1, self.axi3m1]:
            i.ADDR_USER_WIDTH = 10

    @override
    def hwImpl(self):
        r0 = self._reg("r0", def_val=0)
        self.uart.tx(self.uart.rx)
        self.ram1(self.ram0)

        If(self.hsIn.vld,
           r0(self.difIn.p & ~self.difIn.n)
        )
        If(r0,
           self.hsOut(self.hsIn)
        ).Else(
           self.hsOut.data(r0, fit=True),
           self.hsOut.vld(1)
        )

        self.axi3m0(self.axi3s0)
        self.axi3m1(self.axi3s1)


class IpCorePackagerTC(unittest.TestCase):

    @override
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    @override
    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_itIsPossibleToSerializeIpcores(self):
        f = Fifo()
        f.DEPTH = 16

        en0 = Axi4S_en()
        en0.USE_STRB = True
        en0.USE_KEEP = True
        en0.ID_WIDTH = 8
        en0.DEST_WIDTH = 4
        en0.USER_WIDTH = 12

        testHwModules = [
            Axi4S_en(),
            en0,
            AxiLiteEndpoint(HStruct(
                                (uint64_t, "f0"),
                                (uint64_t[10], "arr0")
                            )),
            I2cMasterBitCtrl(),
            f,
            Axi4streamToMem(),
            IpCoreIntfTest(),
        ]
        for u in testHwModules:
            serializeAsIpcore(u, folderName=self.test_dir)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([IpCorePackagerTC("test_sWithStartPadding")])
    suite = testLoader.loadTestsFromTestCase(IpCorePackagerTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
