import shutil
import tempfile
import unittest

from hwt.code import If, connect
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.differential import DifferentialSig
from hwt.interfaces.std import BramPort, Handshaked
from hwt.interfaces.utils import addClkRst
from hwt.serializer.ip_packager.interfaces.std import IP_Handshake
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.shortcuts import serializeAsIpcore
from hwtLib.amba.axi4_streamToMem import Axi4streamToMem
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axis import AxiStream_withUserAndStrb, AxiStream_withId
from hwtLib.amba.axis_comp.en import AxiS_en
from hwtLib.i2c.masterBitCntrl import I2cMasterBitCtrl
from hwtLib.mem.fifo import Fifo
from hwtLib.types.ctypes import uint64_t
from hwtLib.uart.intf import Uart


class Handshaked_withIP(Handshaked):
    def _getIpCoreIntfClass(self):
        return IP_Handshake


class IpCoreIntfTest(Unit):
    def _declr(self):
        addClkRst(self)

        self.ram0 = BramPort()
        self.ram1 = BramPort()
        self.uart = Uart()
        self.hsIn = Handshaked_withIP()
        self.hsOut = Handshaked_withIP()
        self.difIn = DifferentialSig()

    def _impl(self):
        r0 = self._reg("r0", defVal=0)
        self.uart.tx ** self.uart.rx
        self.ram0 ** self.ram1

        If(self.hsIn.vld,
           r0 ** (self.difIn.p & ~self.difIn.n)
        )
        If(r0,
           self.hsOut ** self.hsIn
        ).Else(
           connect(r0, self.hsOut.data, fit=True),
           self.hsOut.vld ** 1
        )


class IpCorePackagerTC(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_itispossibleToSerializeIpcores(self):
        f = Fifo()
        f.DEPTH.set(16)
        testUnits = [AxiS_en(AxiStream_withUserAndStrb),
                     AxiS_en(AxiStream_withId),
                     AxiLiteEndpoint(HStruct(
                         (uint64_t, "f0"),
                         (Array(uint64_t, 10), "arr0")
                                     )),
                     I2cMasterBitCtrl(),
                     f,
                     Axi4streamToMem(),
                     IpCoreIntfTest()
                     ]
        for u in testUnits:
            serializeAsIpcore(u, folderName=self.test_dir)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IpCorePackagerTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(IpCorePackagerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
