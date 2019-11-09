import os
from unittest.case import TestCase

from hwt.hdl.types.array import HArray
from hwt.interfaces.std import Signal
from hwt.serializer.generic.context import SerializerCtx
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
from hwtLib.types.ctypes import uint8_t


# class Interface1d(Unit):
#
#     def _config(self):
#         self.SIZE = Param(3)
#
#     def _declr(self):
#         self.din = Signal(dtype=uint8_t[self.SIZE])
#         self.dout = HObjList([Signal(dtype=uint8_t)._m()
#                               for _ in range(self.SIZE)])
#
#     def _impl(self):
#         for i in range(self.SIZE):
#             o = self.din[i]
#             self.dout[i](o)
# class Interface2d(Unit):
#
#     def _config(self):
#         self.SIZE_X = Param(3)
#         self.SIZE_Y = Param(3)
#
#     def _declr(self):
#         self.din = Signal(dtype=uint8_t[self.SIZE_X][self.SIZE_Y])
#         self.dout = HObjList([
#             HObjList([
#                 Signal(dtype=uint8_t)._m()
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
class InterfaceWithVHDLUnonstrainedArrayImportedType(Unit):
    """
    .. hwt-schematic::
    """
    """

    def _config(self):
        self.SIZE_X = Param(3)

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

        array1d_t = uint8_t[self.SIZE_X]

        def array1d_t_to_vhdl(serializer, t: HArray, ctx: SerializerCtx, declaration=False):
            if declaration:
                return ""
            return "mem(0 to %d)(%d downto 0)" % (t.size, t.element_t.bit_length())

        array1d_t._to_vhdl = array1d_t_to_vhdl
        self.din = Signal(dtype=array1d_t)
        self.dout = HObjList([
            Signal(dtype=uint8_t)._m()
            for _ in range(self.SIZE_X)
        ])

    def _impl(self):
        for d_in, d_out in zip(self.din, self.dout):
            d_out(d_in)


class InterfaceWithArrayTypesTC(TestCase):

    def assert_same_as_file(self, s, file_name: str):
        THIS_DIR = os.path.dirname(os.path.realpath(__file__))
        fn = os.path.join(THIS_DIR, file_name)
        # with open(fn, "w") as f:
        #     f.write(s)
        with open(fn) as f:
            ref_s = f.read()
        self.assertEqual(s, ref_s)

    def test_InterfaceWithVHDLUnonstrainedArrayImportedType(self):
        u = InterfaceWithVHDLUnonstrainedArrayImportedType()
        s = toRtl(u, serializer=VhdlSerializer)
        self.assert_same_as_file(s, "InterfaceWithVHDLUnonstrainedArrayImportedType.vhd")


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(InterfaceWithArrayTypesTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    # print(toRtl(Interface1d()))
    # print(toRtl(Interface2d()))
    print(toRtl(InterfaceWithVHDLUnonstrainedArrayImportedType()))

