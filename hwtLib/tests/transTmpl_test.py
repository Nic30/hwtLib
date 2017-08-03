import unittest
from hwt.hdlObjects.types.struct import HStruct
from hwtLib.types.ctypes import uint8_t
from hwt.hdlObjects.transTmpl import TransTmpl


class TransTmpl_TC(unittest.TestCase):
    def test_walkFlatten_struct(self):
        t = HStruct((uint8_t, "a"),
                    (uint8_t, "b"),
                    (uint8_t, "c"))
        trans = TransTmpl(t)
        self.assertEqual(len(list(trans.walkFlatten())), 3)

    def test_walkFlatten_arr(self):
        t = HStruct((uint8_t[4], "a"))
        trans = TransTmpl(t)
        self.assertEqual(len(list(trans.walkFlatten())), 4)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TransTmpl_TC('test_walkFlatten_arr'))
    suite.addTest(unittest.makeSuite(TransTmpl_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)