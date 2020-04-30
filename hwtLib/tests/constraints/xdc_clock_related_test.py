

import os
from tempfile import TemporaryDirectory
import unittest

from hwt.serializer.store_manager import SaveToFilesFlat
from hwt.serializer.vhdl import Vhdl2008Serializer
from hwt.serializer.xdc.serializer import XdcSerializer
from hwt.synthesizer.utils import toRtl
from hwtLib.mem.fifoAsync import FifoAsync


class ConstraintsXdcClockRelatedTC(unittest.TestCase):
    __FILE__ = __file__

    def assert_constraints_file_eq(self, u, file_name):
        THIS_DIR = os.path.dirname(os.path.realpath(self.__FILE__))
        ref_f_name = os.path.join(THIS_DIR, file_name)
        with TemporaryDirectory() as build_root:
            saver = SaveToFilesFlat(Vhdl2008Serializer, build_root)
            toRtl(u, saver)

            f_name = os.path.join(build_root, "constraints" + XdcSerializer.fileExtension)
            with open(f_name) as f:
                s = f.read()
            # with open(ref_f_name, "w") as f:
            #     f.write(s)

        with open(ref_f_name) as f:
            ref_s = f.read()
        self.assertEqual(s, ref_s)

    def test_FifoAsync(self):
        u = FifoAsync()
        u.DEPTH = 8
        self.assert_constraints_file_eq(u, "FifoAsync.xdc")


if __name__ == '__main__':
    unittest.main()
