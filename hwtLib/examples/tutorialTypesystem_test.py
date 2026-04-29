#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import inf
import unittest

from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsCastUtils import fitTo_t
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import STR, FLOAT64, BIT_N, BIT
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.union import HUnion
from hwt.synthesizer.exceptions import TypeConversionErr
from hwtLib.types.ctypes import uint8_t, int8_t, uint16_t
from pyMathBitPrecise.bit_utils import ValidityError


class TutorialTypesystemTC(unittest.TestCase):

    def test_HBits_const(self):
        # :note: The content of this function is a small tutorial about the HWT typesystem

        # :note: HBits is hwt type class which is used to describe integers and bit vectors
        #  this is a definition of the 4bit unsigned int
        uint4_t = HBits(4, signed=False)
        # the type has own methods and properties
        assert uint4_t.bit_length() == 4
        assert uint4_t.signed == False
        assert uint4_t.strict_sign == True
        assert uint4_t.strict_width == True
        assert uint4_t.is_bigendian == False
        assert uint4_t.name is None

        # creating a value of that specific type,
        _1 = uint4_t.from_py(1)

        # the value has own __repr__ method defined which simplifies debugging
        assert repr(_1) == "<HBitsConst u4 1>"
        # the value can also be converted back to python
        assert int(_1) == 1
        assert _1.to_py() == 1

        # value object has backward reference to its type
        assert _1._dtype is uint4_t
        assert isinstance(_1, uint4_t.getConstCls()) and _1.__class__ is HBitsConst

        # value type and range is checked (and error raised)
        # self.assertRaises(expected_exception)
        with self.assertRaises(ValueError):
            uint4_t.from_py(256)

        with self.assertRaises(ValueError):
            uint4_t.from_py(-1)

        # the value does not needs to be fully defined
        v = uint4_t.from_py(0b1, vld_mask=0b1)  # "XXX1"
        assert not v._is_full_valid()
        assert v._is_partially_valid()
        with self.assertRaises(ValidityError):
            int(v)
        assert v.to_py() is None

        v = uint4_t.from_py(None)  # "XXXX"
        assert not v._is_full_valid()
        assert not v._is_partially_valid()
        with self.assertRaises(ValidityError):
            int(v)
        assert v.to_py() is None

        # value object does implement all type operators
        assert int(_1 + _1) == 2

        # the size of the bit vector has to be >0
        # (the best practise is not to use 0 size objects entirely
        #  and python allows you to build interfaces and other objects dynamically
        #  so there is no reason to support 0 size vectors)
        with self.assertRaises(AssertionError):
            HBits(0)

        # SV wire/reg
        # VHDL std_logic
        HBits(1)
        # SV wire[0:0]/reg[0:0]
        # VHDL std_logic and std_logic_vector(0 downto 0)
        HBits(1, force_vector=True)

        # SV wire [8-1:0] / reg [8-1:0]
        # VHDL std_logic_vector(8-1 downto 0)
        HBits(8, signed=None)
        # SV wire [8-1:0] / reg [8-1:0]
        # VHDL unsigned(8-1 downto 0)
        HBits(8, signed=False)
        # SV wire signed [8-1:0] / reg signed [8-1:0]
        # VHDL signed(8-1 downto 0)
        HBits(8, signed=True)

    def test_HEnum_const(self):
        # The HEnum is an enumeration type. It can be declared using its name an all possible values
        t = HEnum("t", ["idle", "work", "end"])
        assert repr(t) == "<HEnum t>"

        # The list of all available value names is stored in _allValues property.
        assert t._allValues == ('idle', 'work', 'end')
        # The bit length corresponds to a length of a binary encoded index of a value name.
        assert t.bit_length() == 2
        # The values of the enum are provided as a properties of the enum type.
        assert repr(t.idle) == "<HEnumConst 'idle'>"

    def test_HString_const(self):
        # String type meant for backward compatibility with the SystemVerilog and VHDL
        v = STR.from_py("abc")
        assert v.to_py() == "abc"

    def test_HFloat_const(self):
        # HFloat can be used to define IEEE 754 floating datatypes
        assert FLOAT64.exponent_w == 11
        assert FLOAT64.mantisa_w == 52
        v = FLOAT64.from_py(0.5)
        assert v.to_py() == 0.5

    def test_HArray_const(self):
        # HArray is a type class used to define arrays.
        # Although you can create an array by instantiation of HArray type class
        # directly the common way how to define an array is to use index [] operator
        # on any HdlType
        arr_t = uint8_t[3]
        assert isinstance(arr_t, HArray)
        assert repr(arr_t) == "<HBits, 8bits, unsigned>[3]"
        # The size and type of element can be accessed
        assert arr_t.size == 3
        assert arr_t.element_t is uint8_t

        # The value can be constructed from a sequence
        v0 = arr_t.from_py([0, 1, 2])
        self.assertEqual(repr(v0), "<HArrayConst {0: <HBitsConst u8 0>, 1: <HBitsConst u8 1>, 2: <HBitsConst u8 2>}>")
        assert v0.to_py() == [0, 1, 2]

        # The value constructed from None is entirely invalid
        v1 = arr_t.from_py(None)
        assert repr(v1) == "<HArrayConst {}, mask 0>"

        # Alternatively the dictionary (index-value) can be
        # used to initialize just some elements
        v2 = arr_t.from_py({0: 10, 2: 20})
        assert v2.to_py() == [10, None, 20]
        v3 = arr_t.from_py({0: 10, 1: uint8_t.from_py(0, vld_mask=0x03), 2: 20})
        assert v3.to_py() == [10, None, 20]
        # the value supports indexing as expected
        assert int(v2[0]) == 10
        v2[1] = 11
        assert v2.to_py() == [10, 11, 20]

    def test_HStruct_const(self):
        # HStruct is HWT struct type, it behaves like packed C struct,
        # however it may contain the members of variable size which is a difference
        # compared to clasic C struct type.
        t = HStruct(
            (uint8_t, "a"),
            (uint8_t, None),  # padding
            (uint8_t, "b"),
        )
        v = t.from_py({"a": 10})
        # {
        #     a: <HBitsConst 10>
        #     b: <HBitsConst 0, mask 0>
        # }
        assert int(v.a) == 10
        assert v._dtype.bit_length() == 24

        tmpl = TransTmpl(t)  # transaction planning
        self.assertEqual(repr(tmpl),
        "<TransTmpl start:0, end:24\n"
        "    <TransTmpl name:a, start:0, end:8>\n"
        "    <TransTmpl name:b, start:16, end:24>\n"
        ">")
        tmpAt16b = list(FrameTmpl.framesFromTransTmpl(tmpl, 16))  # transaction plan
        self.assertEqual(repr(tmpAt16b),
                "[<FrameTmpl start:0, end:32\n"
                "     15             0\n"
                "     -----------------\n"
                "0    |XXXXXXX|   a   |\n"  # XXX is padding inside of frame
                "1    |XXXXXXX|   b   |\n"  # XXX is padding at the end of frame
                "     -----------------\n"
                ">]")

    def test_HUnion_const(self):
        t = HUnion(
            (int8_t, "signed"),
            (uint8_t, "unsigned"),
        )
        v = t.from_py(("signed", -1))
        self.assertEqual(repr(v),
            "{\n"
            "    signed: <HBitsConst i8 -1>\n"
            "    unsigned: <HBitsConst u8 255>\n"
            "}")

    def test_HStream_const(self):
        t = HStruct(
            (uint8_t, "header"),
            (HStream(uint8_t, frame_len=(1, inf)), "payload"),
            (uint8_t, "footer"),
        )
        self.assertEqual(repr(t),
            "struct {\n"
            "    <HBits, 8bits, unsigned> header\n"
            "    <HStream len:(1, inf), align:(0,)\n"
            "        <HBits, 8bits, unsigned>> payload\n"
            "    <HBits, 8bits, unsigned> footer\n"
            "}")

    def test_casting(self):
        v = uint8_t[2].from_py([1, 2])
        structAB = HStruct(
            (uint8_t, "a"),
            (uint8_t, "b"),
        )
        structABC = HStruct(
            (uint8_t, "a"),
            (uint8_t, "b"),
            (uint8_t, "c"),
        )
        vAsStruct = v._reinterpret_cast(structAB)
        assert vAsStruct.a.to_py() == 1
        assert vAsStruct.b.to_py() == 2
        assert vAsStruct._reinterpret_cast(uint16_t).to_py() == (1 | (2 << 8))

        with self.assertRaises(TypeConversionErr):
            v._reinterpret_cast(structABC)  # requires to be of same width

        # int is auto casted to uint8_t
        v = 1 + uint8_t.from_py(1)
        assert v.to_py() == 2
        v = uint8_t.from_py(1) + 1
        assert v.to_py() == 2

        with self.assertRaises(TypeError):
            uint8_t.from_py(1) + uint16_t.from_py(1)

        v = uint8_t.from_py(1) + fitTo_t(uint16_t.from_py(1), uint8_t)
        assert v.to_py() == 2

        v = uint16_t.from_py(0x99)
        with self.assertRaises(TypeConversionErr):
            v._auto_cast(uint8_t)  # must be of same width or has strict_width=False

        assert v._explicit_cast(uint8_t).to_py() == 0x99
        with self.assertRaises(TypeConversionErr):
            v._reinterpret_cast(uint8_t)  # must be of same width

        v = structAB.from_py({"a": 0x21, "b": 0x43})

        structAB4b = HStruct(
            (HBits(4), "a0"),
            (HBits(4), "a1"),
            (HBits(4), "b0"),
            (HBits(4), "b1"),
        )
        with self.assertRaises(TypeConversionErr):
            v._auto_cast(structAB4b)  # only same to same
        with self.assertRaises(TypeConversionErr):
            v._explicit_cast(structAB4b)  # only same to same

        v2 = v._reinterpret_cast(structAB4b)  # only same to same
        self.assertDictEqual(v2.to_py(), {"a0": 1, "a1": 2, "b0": 3, "b1": 4})

    def test_HBits_negated(self):
        v = BIT_N.from_py(1)
        # the negation flag affects only a single operand, _isOn()
        # and is also only supported operand if negated=True
        assert int(v) == 1
        assert bool(v) == True

        self.assertEqual(v._isOn()._dtype, BIT)
        self.assertEqual(bool(v._isOn()), False)
        with self.assertRaises(TypeError):
            ~v
        with self.assertRaises(TypeError):
            v & 1
        with self.assertRaises(TypeError):
            v + 1


if __name__ == '__main__':
    unittest.main()
