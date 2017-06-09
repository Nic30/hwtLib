import shutil
import tempfile
import unittest

from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.struct import HStruct
from hwt.serializer.ip_packager.packager import Packager
from hwtLib.amba.axi4_streamToMem import Axi4streamToMem
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axis import AxiStream_withUserAndStrb, AxiStream_withId
from hwtLib.amba.axis_comp.en import AxiS_en
from hwtLib.i2c.masterBitCntrl import I2cMasterBitCtrl
from hwtLib.mem.fifo import Fifo
from hwtLib.types.ctypes import uint64_t


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
                     Axi4streamToMem()
                     ]
        for u in testUnits:
            p = Packager(u)
            p.createPackage(self.test_dir)
            

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IpCorePackagerTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(IpCorePackagerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
