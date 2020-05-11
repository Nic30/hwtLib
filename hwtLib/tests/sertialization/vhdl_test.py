import unittest

from hwt.code import Concat
from hwt.hdl.typeShortcuts import hBit, vec
from hwt.interfaces.std import VectSignal
from hwt.synthesizer.unit import Unit
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class TernaryInConcatExample(Unit):
    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)
        self.c = VectSignal(32)._m()

    def _impl(self):
        a = self.a
        b = self.b
        self.c(
            Concat(
                hBit(1),
                vec(7, 3),
                a != b,
                a < b,
                a <= b,
                a._eq(b),
                a >= b,
                a > b,
                vec(0, 22),
                )
            )


class Vhdl2008Serializer_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_add_to_slice_vhdl(self):
        u = TernaryInConcatExample()
        self.assert_serializes_as_file(u, "TernaryInConcatExample.vhd")


if __name__ == '__main__':
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(TernaryInConcatExample()))
    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(Vhdl2008Serializer_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
