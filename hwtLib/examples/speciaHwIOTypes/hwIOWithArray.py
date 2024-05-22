#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.hdlAst._expr import HdlValueId, HdlOp, HdlOpType
from hdlConvertorAst.translate.verilog_to_basic_hdl_sim_model.utils import hdl_index, \
    hdl_downto
from hwt.hObjList import HObjList
from hwt.hwParam import HwParam
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.serializer.vhdl import ToHdlAstVhdl2008
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.types.ctypes import uint8_t


# class Interface1d(HwModule):
#
#     def _config(self):
#         self.SIZE = HwParam(3)
#
#     def _declr(self):
#         self.din = HwIOSignal(dtype=uint8_t[self.SIZE])
#         self.dout = HObjList([HwIOSignal(dtype=uint8_t)._m()
#                               for _ in range(self.SIZE)])
#
#     def _impl(self):
#         for i in range(self.SIZE):
#             o = self.din[i]
#             self.dout[i](o)
# class Interface2d(HwModule):
#
#     def _config(self):
#         self.SIZE_X = HwParam(3)
#         self.SIZE_Y = HwParam(3)
#
#     def _declr(self):
#         self.din = HwIOSignal(dtype=uint8_t[self.SIZE_X][self.SIZE_Y])
#         self.dout = HObjList([
#             HObjList([
#                 HwIOSignal(dtype=uint8_t)._m()
#                 for _ in range(self.SIZE_Y)])
#             for _ in range(self.SIZE_X)
#         ])
#
#     def _impl(self):
#         # for x in range(self.SIZE_X):
#         #     for y in range(self.SIZE_Y):
#         #         o = self.din[x][y]
#         #         self.dout[x][y](o)
#
#         for x_in, x_out in zip(self.din, self.dout):
#             for d_in, d_out in zip(x_in, x_out):
#                 d_out(d_in)
def example_use_vhdl_declared_array1d(SIZE_X):
    array1d_t = uint8_t[SIZE_X]

    def array1d_t_to_vhdl(to_hdl: ToHdlAstVhdl2008, declaration=False):
        if not isinstance(to_hdl, ToHdlAstVhdl2008):
            raise NotImplementedError()

        if declaration:
            raise ValueError(
                "_as_hdl_requires_def specifies that this should not be required")
        # "mem(0 to %d)(%d downto 0)" % (t.size, t.element_t.bit_length() - 1)
        _int = to_hdl.as_hdl_int
        size = HdlOp(HdlOpType.TO, [_int(0), _int(int(array1d_t.size))])
        e_width = hdl_downto(
            _int(array1d_t.element_t.bit_length() - 1), _int(0))
        return hdl_index(hdl_index(HdlValueId("mem"), size), e_width)

    def array1d_t_as_hdl_requires_def(to_hdl: ToHdlAstVhdl2008, other_types: list):
        return False

    array1d_t._as_hdl = array1d_t_to_vhdl
    array1d_t._as_hdl_requires_def = array1d_t_as_hdl_requires_def

    return array1d_t


class HwIOWithVHDLUnconstrainedArrayImportedType(HwModule):

    def _config(self):
        self.SIZE_X = HwParam(3)

    def _declr(self):
        # lets suppose that there is some package which has vhdl type defined as:
        #   type data_vector is array (natural range <>, natural range <>) of integer;
        #   type mem is array(natural range <>) of std_logic_vector;
        # We would like to use this type in HWT, but there is no explicit support for vhdl 2008
        # unconstrained multi dim. arrays or external VHDL types.
        # But we need to our interface with type like this:
        #   signal our_interface: mem(0 to 15)(7 downto 0);
        # so we are actually able to connect this component to existing design.

        # In this example we will mock the type with HWT array type and override
        # serialization so we will get desired type name in VHDL.
        array1d_t = example_use_vhdl_declared_array1d(self.SIZE_X)

        self.din = HwIOSignal(dtype=array1d_t)
        self.dout = HObjList([
            HwIOSignal(dtype=uint8_t)._m()
            for _ in range(self.SIZE_X)
        ])

    def _impl(self):
        for d_in, d_out in zip(self.din, self.dout):
            d_out(d_in)


class HwIOWithVHDLUnconstrainedArrayImportedType2(HwModule):

    def _config(self):
        self.SIZE_X = HwParam(3)

    def _declr(self):
        array1d_t = example_use_vhdl_declared_array1d(self.SIZE_X)

        self.dout = HwIOSignal(dtype=array1d_t)._m()
        self.din = HObjList([
            HwIOSignal(dtype=uint8_t)
            for _ in range(self.SIZE_X)
        ])

    def _impl(self):
        for d_in, d_out in zip(self.din, self.dout):
            d_out(d_in)


class HwIOWithArrayTypesTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_HwIOWithVHDLUnconstrainedArrayImportedType(self):
        m = HwIOWithVHDLUnconstrainedArrayImportedType()
        self.assert_serializes_as_file(
            m, "HwIOWithVHDLUnconstrainedArrayImportedType.vhd")

    def test_HwIOWithVHDLUnconstrainedArrayImportedType2(self):
        m = HwIOWithVHDLUnconstrainedArrayImportedType2()
        self.assert_serializes_as_file(
            m, "HwIOWithVHDLUnconstrainedArrayImportedType2.vhd")


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(HwIOWithArrayTypesTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    # print(to_rtl_str(Interface1d()))
    # print(to_rtl_str(Interface2d()))
    # print(to_rtl_str(HwIOWithVHDLUnconstrainedArrayImportedType()))
    # print(to_rtl_str(HwIOWithVHDLUnconstrainedArrayImportedType2()))
