import unittest
from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint8_t, uint16_t
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.union import HUnion

union0 = HUnion(
            (HStruct(
                (uint8_t, "a0"),
                (uint8_t, "a1"),
             ), "a"),
            (uint16_t, "b"),
            )
union0_str = """<TransTmpl start:0, end:16
    <TransTmpl name:a, start:0, end:16
        <TransTmpl name:a0, start:0, end:8>
        <TransTmpl name:a1, start:8, end:16>
    >
    <OR>
    <TransTmpl name:b, start:0, end:16>
>"""


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

    def test__repr__union(self):
        s = repr(TransTmpl(union0))
        self.assertEqual(s, union0_str)

    def test_walkFlatten_union(self):
        trans = TransTmpl(union0)
        fl = list(trans.walkFlatten())
        self.assertEqual(len(fl), 1)
        children = list(fl[0].walkFlattenChilds())
        self.assertEqual(len(children), 2)

        self.assertEqual(len(list(children[0])), 2)
        self.assertEqual(len(list(children[1])), 1)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TransTmpl_TC('test_walkFlatten_arr'))
    suite.addTest(unittest.makeSuite(TransTmpl_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)