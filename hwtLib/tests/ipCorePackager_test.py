import shutil
import tempfile
import unittest

from hwt.code import If, connect
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.differential import DifferentialSig
from hwt.interfaces.std import BramPort, Handshaked
from hwt.interfaces.utils import addClkRst
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import serializeAsIpcore
from hwt.interfaces.std_ip_defs import IP_Handshake

from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axi_comp.axi4_streamToMem import Axi4streamToMem
from hwtLib.amba.axis_comp.en import AxiS_en
from hwtLib.mem.fifo import Fifo
from hwtLib.peripheral.i2c.masterBitCntrl import I2cMasterBitCtrl
from hwtLib.peripheral.uart.intf import Uart
from hwtLib.types.ctypes import uint64_t


class Handshaked_withIP(Handshaked):
    def _getIpCoreIntfClass(self):
        return IP_Handshake


class IpCoreIntfTest(Unit):
    def _declr(self):
        addClkRst(self)

        self.ram0 = BramPort()
        self.ram1 = BramPort()._m()
        self.uart = Uart()._m()
        self.hsIn = Handshaked_withIP()
        self.hsOut = Handshaked_withIP()._m()
        self.difIn = DifferentialSig()
        self.axi3s0 = Axi3()
        self.axi3m0 = Axi3()._m()

        self.axi3s1 = Axi3()
        self.axi3m1 = Axi3()._m()
        for i in [self.axi3s1, self.axi3m1]:
            i.ADDR_USER_WIDTH = 10

    def _impl(self):
        r0 = self._reg("r0", def_val=0)
        self.uart.tx(self.uart.rx)
        self.ram1(self.ram0)

        If(self.hsIn.vld,
           r0(self.difIn.p & ~self.difIn.n)
        )
        If(r0,
           self.hsOut(self.hsIn)
        ).Else(
           connect(r0, self.hsOut.data, fit=True),
           self.hsOut.vld(1)
        )

        self.axi3m0(self.axi3s0)
        self.axi3m1(self.axi3s1)


class IpCorePackagerTC(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_itIsPossibleToSerializeIpcores(self):
        f = Fifo()
        f.DEPTH = 16

        en0 = AxiS_en()
        en0.USE_STRB = True
        en0.USE_KEEP = True
        en0.ID_WIDTH = 8
        en0.DEST_WIDTH = 4
        en0.USER_WIDTH = 12

        testUnits = [AxiS_en(),
                     en0,
                     AxiLiteEndpoint(HStruct(
                                         (uint64_t, "f0"),
                                         (uint64_t[10], "arr0")
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
