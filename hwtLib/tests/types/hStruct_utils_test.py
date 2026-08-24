import unittest

from hwt.hdl.types.struct import HStruct, HStructFromClass
from hwt.hdl.types.bits import HBits


class Struct0(HStructFromClass):
    f1: HBits(16)
    f0: HBits(8)


class Struct1(HStructFromClass):
    __: HBits(8)
    f0: HBits(8)
    f1: HBits(16)


class Struct2(Struct1):
    f2: HBits(32)


class HStructFromClassTC(unittest.TestCase):

    def test_struct0_type_and_name(self):
        t = Struct0.asHdlType()
        self.assertIsInstance(t, HStruct)
        self.assertEqual(t.name, "Struct0")

    def test_struct0_fields_count(self):
        t = Struct0.asHdlType()
        self.assertEqual(len(t.fields), 2)

    def test_struct0_fields_names_and_types(self):
        t = Struct0.asHdlType()
        fields_info = [(f.name, f.dtype) for f in t.fields]
        self.assertEqual(
            fields_info,
            [("f1", HBits(16)), ("f0", HBits(8))],
        )

    def test_struct1(self):
        t = Struct1.asHdlType()
        fields_info = [(f.name, f.dtype) for f in t.fields]
        self.assertEqual(
            fields_info,
            [(None, HBits(8)), ("f0", HBits(8)), ("f1", HBits(16)), ],
        )
        t2 = Struct1.asHdlType()
        self.assertIs(t2, t)

    def test_struct2(self):
        t = Struct2.asHdlType()
        fields_info = [(f.name, f.dtype) for f in t.fields]
        self.assertEqual(
            fields_info,
            [(None, HBits(8)), ("f0", HBits(8)), ("f1", HBits(16)), ("f2", HBits(32)), ],
        )


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(HStructFromClassTC)
    # suite = unittest.TestSuite([HStructFromClassTC("test_struct0_fields_count")])
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

