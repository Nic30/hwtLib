import unittest

from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.bits import HBits


@HStruct.fromClass
class Struct0:
    f1: HBits(16)
    f0: HBits(8)


@HStruct.fromClass
class Struct1:
    __: HBits(8)
    f1: HBits(16)
    f0: HBits(8)


@HStruct.fromClass(ignoredPaddingName="_pad")
class Struct2:
    _pad: HBits(8)
    f1: HBits(16)
    f0: HBits(8)


class HStructFromClassTC(unittest.TestCase):

    def test_struct0_type_and_name(self):
        self.assertIsInstance(Struct0, HStruct)
        self.assertEqual(Struct0.name, "Struct0")

    def test_struct0_fields_count(self):
        self.assertEqual(len(Struct0.fields), 2)

    def test_struct0_fields_names_and_types(self):
        fields_info = [(f.name, f.dtype) for f in Struct0.fields]
        self.assertEqual(
            fields_info,
            [("f1", HBits(16)), ("f0", HBits(8))],
        )

    def test_struct0_first_field_name(self):
        # Original test had a small typo: `len(Struct0.fields[1].name)`;
        # here we check the actual field name.
        self.assertEqual(Struct0.fields[0].name, "f1")

    def test_struct1_padding_field_is_none(self):
        self.assertIsNone(Struct1.fields[0].name)

    def test_struct2_custom_padding_name(self):
        self.assertIsNone(Struct2.fields[0].name)


if __name__ == "__main__":
    unittest.main()