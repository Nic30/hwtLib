import unittest

from pyMathBitPrecise.bit_utils import mask

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct


struct0_t = HStruct(
    (HBits(8), "v0"),
    (HBits(8), "v1")
)


class CastTc(unittest.TestCase):

    def test_reinterpret_bits_to_array(self):
        v = HBits(2 * 8).from_py(mask(2 * 8) - 1)
        v0 = v._reinterpret_cast(HBits(8)[2])
        self.assertSequenceEqual([int(v1) for v1 in v0],
                                 [0xff - 1, 0xff])

    def test_reinterpret_array_to_bits(self):
        v = HBits(8)[2].from_py([0xff - 1, 0xff])
        v0 = v._reinterpret_cast(HBits(2 * 8))
        self.assertEqual(int(v0), mask(2 * 8) - 1)

    def test_reinterpret_array_to_struct(self):
        v = HBits(8)[2].from_py([0xff, 0xff - 1])
        v0 = v._reinterpret_cast(struct0_t)
        self.assertEqual(int(v0.v0), 0xff)
        self.assertEqual(int(v0.v1), 0xff - 1)

    def test_reinterpret_struct_to_array(self):
        v = struct0_t.from_py({"v0": 0xff, "v1": 0xff - 1})
        v0 = v._reinterpret_cast(HBits(8)[2])
        self.assertSequenceEqual([int(v1) for v1 in v0],
                                 [0xff, 0xff - 1])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([CastTc("test_reinterpret_bits_to_array")])
    suite = testLoader.loadTestsFromTestCase(CastTc)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
