import unittest

from pyMathBitPrecise.bit_utils import mask

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct


struct0_t = HStruct(
    (Bits(8), "v0"),
    (Bits(8), "v1")
)


class CastTc(unittest.TestCase):

    def test_reinterpret_bits_to_array(self):
        v = Bits(2 * 8).from_py(mask(2 * 8) - 1)
        v0 = v._reinterpret_cast(Bits(8)[2])
        self.assertSequenceEqual([int(v1) for v1 in v0],
                                 [0xff - 1, 0xff])

    def test_reinterpret_array_to_bits(self):
        v = Bits(8)[2].from_py([0xff - 1, 0xff])
        v0 = v._reinterpret_cast(Bits(2 * 8))
        self.assertEqual(int(v0), mask(2 * 8) - 1)

    def test_reinterpret_array_to_struct(self):
        v = Bits(8)[2].from_py([0xff, 0xff - 1])
        v0 = v._reinterpret_cast(struct0_t)
        self.assertEqual(int(v0.v0), 0xff)
        self.assertEqual(int(v0.v1), 0xff - 1)

    def test_reinterpret_struct_to_array(self):
        v = struct0_t.from_py({"v0": 0xff, "v1": 0xff - 1})
        v0 = v._reinterpret_cast(Bits(8)[2])
        self.assertSequenceEqual([int(v1) for v1 in v0],
                                 [0xff, 0xff - 1])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CastTc('test_reinterpret_bits_to_array'))
    suite.addTest(unittest.makeSuite(CastTc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
