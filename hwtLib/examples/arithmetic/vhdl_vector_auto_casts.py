from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class VhdlVectorAutoCastExample(Unit):

    def _declr(self):
        std_logic = Bits(1)
        std_logic_vector_0 = Bits(1, force_vector=True)

        self.a = Signal(dtype=std_logic)
        self.b = Signal(dtype=std_logic)._m()

        self.c = Signal(dtype=std_logic_vector_0)._m()

        self.d = Signal(dtype=std_logic_vector_0)
        self.e = Signal(dtype=std_logic)._m()

        self.f = Signal(dtype=std_logic)
        self.g = Signal(dtype=std_logic_vector_0)

        self.i = Signal(dtype=std_logic)._m()

        self.j = Signal(dtype=std_logic)._m()

    def _impl(self):
        # no conversion
        self.b(self.a)

        # std_logic -> std_logic_vector
        self.c(self.a)
        # std_logic_vector -> std_logic
        self.e(self.d)

        # unsigned(std_logic)  + unsigned(std_logic_vector) -> std_logic_vector ->  std_logic
        self.i(self.f + self.g)

        # unsigned(std_logic)  + unsigned(std_logic_vector) -> std_logic_vector ->  std_logic
        self.j(self.g + self.f)


class VhdlVectorAutoCastExampleTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_vhdl(self):
        u = VhdlVectorAutoCastExample()
        self.assert_serializes_as_file(u, "VhdlVectorAutoCastExample.vhd")


if __name__ == '__main__':
    from hwt.synthesizer.utils import to_rtl_str
    from hwt.serializer.vhdl import Vhdl2008Serializer

    u = VhdlVectorAutoCastExample()
    print(to_rtl_str(u, Vhdl2008Serializer))

    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(VhdlVectorAutoCastExampleTC('test_vhdl'))
    suite.addTest(unittest.makeSuite(VhdlVectorAutoCastExampleTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
