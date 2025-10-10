#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.hwIOs.std import HwIORegCntrl, HwIOBramPort_noClk
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.typePath import TypePath
from hwtLib.types.ctypes import uint8_t

struct0 = HStruct(
    (uint8_t, "f0"),
    (HStruct(
        (uint8_t, "f1"),
        (uint8_t, "f2")
    )[4], "arr0")
)
# struct0 = HStruct(
#        (uint8_t[2], "arr0")
#    )


class ListOfHwIOsSample4(HwModule):
    """
    Example with HObjList of interfaces where interfaces are instances of HwIOStruct
    which is interface dynamically generated from c-like structure description

    .. hwt-autodoc::
    """

    @staticmethod
    def shouldEnterFn(field_path: TypePath):
        return False, True

    def _mkFieldInterface(self, structHwIO: HStruct, field: HStructField):
        t = field.dtype

        if isinstance(t, HBits):
            p = HwIORegCntrl()
            dw = t.bit_length()
        elif isinstance(t, HArray):
            field_path = structHwIO._field_path / field.name
            if self.shouldEnterFn(field_path)[0]:
                if isinstance(t.element_t, HBits):
                    p = HwIOArray(HwIORegCntrl() for _ in range(int(t.size)))
                    dw = t.element_t.bit_length()
                else:
                    p = HwIOArray([HwIOStruct(
                        t.element_t,
                        field_path,
                        instantiateFieldFn=self._mkFieldInterface)
                        for _ in range(int(t.size))])
                    return p
            else:
                p = HwIOBramPort_noClk()
                dw = t.element_t.bit_length()
                p.ADDR_WIDTH = log2ceil(int(t.size) - 1)
        else:
            raise NotImplementedError(t)

        p.DATA_WIDTH = dw

        return p

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.a = HwIOArray(
            HwIOStruct(
                struct0,
                tuple(),
                instantiateFieldFn=self._mkFieldInterface)
            for _ in range(3))
        self.b = HwIOArray(
            HwIOStruct(
                struct0,
                tuple(),
                instantiateFieldFn=self._mkFieldInterface)
            for _ in range(3))._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class ListOfHwIOsSample4b(ListOfHwIOsSample4):
    """
    .. hwt-autodoc::
    """

    @staticmethod
    @override
    def shouldEnterFn(field_path):
        return True, True


class ListOfHwIOsSample4c(ListOfHwIOsSample4b):
    """
    .. hwt-autodoc::
    """

    @override
    def hwImpl(self):
        for a, b in zip(self.a, self.b):
            b(a)


class ListOfHwIOsSample4d(ListOfHwIOsSample4b):
    """
    .. hwt-autodoc::
    """

    @override
    def hwImpl(self):
        for a, b in zip(self.a, self.b):
            b.f0(a.f0)
            for a_arr, b_arr in zip(a.arr0, b.arr0):
                b_arr(a_arr)


class ListOfHwIOsSample4TC(SimTestCase):

    @override
    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_ListOfHwIOsSample4b_HwIOIterations(self):
        dut = ListOfHwIOsSample4d()
        self.compileSimAndStart(dut)

        i = 0
        for a in dut.a:
            for _ in a.arr0:
                i += 1
        self.assertValEqual(i, 3 * 4)

        i = 0
        for hwIO in dut.a:
            i += 1
            a = 0
            for _ in hwIO.arr0:
                a += 1
            self.assertValEqual(a, 4)

        self.assertValEqual(i, 3)

    def _test(self, dut: HwModule):
        self.compileSimAndStart(dut)
        r = self._rand.getrandbits

        def randInts():
            return [r(8) for _ in range(r(2) + 1)]

        # [channel][dataIndex]
        f0_in = []
        f0_out = []

        # [channel][arr0Index][dataIndex]
        f1_in = []
        f1_out = []
        f2_in = []
        f2_out = []

        for i in range(3):
            a = dut.a[i]
            b = dut.b[i]
            _f0_in = randInts()
            _f0_out = randInts()

            a.f0._ag.dout.extend(_f0_out)
            b.f0._ag.din.extend(_f0_in)

            f0_in.append(_f0_in)
            f0_out.append(_f0_out)

            arr_f1_in = []
            arr_f1_out = []
            arr_f2_in = []
            arr_f2_out = []
            for i2 in range(4):
                _a = a.arr0[i2]
                _b = b.arr0[i2]
                _f1_in = randInts()
                _f2_in = randInts()
                _f1_out = randInts()
                _f2_out = randInts()

                _a.f1._ag.dout.extend(_f1_out)
                arr_f1_out.append(_f1_out)

                _b.f1._ag.din.extend(_f1_in)
                arr_f1_in.append(_f1_in)

                _a.f2._ag.dout.extend(_f2_out)
                arr_f2_out.append(_f2_out)

                _b.f2._ag.din.extend(_f2_in)
                arr_f2_in.append(_f2_in)

            f1_out.append(arr_f1_out)
            f1_in.append(arr_f1_in)
            f2_out.append(arr_f2_out)
            f2_in.append(arr_f2_in)

        self.runSim(100 * Time.ns)

        emp = self.assertEmpty
        eq = self.assertValSequenceEqual

        def dinEq(regCntrl, data, *msg):
            """
            check if data on din signal are as expected
            """
            self.assertValSequenceEqual(list(regCntrl._ag.din)[0:len(data)], data, *msg)

        for i, (_f0_in, _f0_out, arr_f1_in, arr_f1_out, arr_f2_in,
                arr_f2_out, a, b) in enumerate(zip(
                f0_in, f0_out, f1_in, f1_out, f2_in,
                f2_out, dut.a, dut.b)):

            emp(a.f0._ag.dout, i)
            dinEq(a.f0, _f0_in, i)

            eq(b.f0._ag.dout, _f0_out, i)
            emp(b.f0._ag.din, i)

            for i2, (a_arr, b_arr, _f1_in, _f1_out, _f2_in, _f2_out) in enumerate(zip(
                    a.arr0, b.arr0,
                    arr_f1_in,
                    arr_f1_out,
                    arr_f2_in,
                    arr_f2_out)):

                emp(a_arr.f1._ag.dout, (i, i2))
                eq(b_arr.f1._ag.dout, _f1_out, (i, i2))

                emp(b_arr.f1._ag.din, (i, i2))
                dinEq(a_arr.f1, _f1_in, (i, i2))

                emp(a_arr.f2._ag.dout, (i, i2))
                eq(b_arr.f2._ag.dout, _f2_out, (i, i2))

                emp(b_arr.f2._ag.din, (i, i2))
                dinEq(a_arr.f2, _f2_in, (i, i2))

    def test_ListOfHwIOsSample4b(self):
        dut = ListOfHwIOsSample4b()
        self._test(dut)

    def test_ListOfHwIOsSample4c(self):
        dut = ListOfHwIOsSample4c()
        self._test(dut)

    def test_ListOfHwIOsSample4d(self):
        dut = ListOfHwIOsSample4d()
        self._test(dut)


if __name__ == "__main__":
    import unittest

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ListOfHwIOsSample4TC("test_ListOfHwIOsSample4b_intfIterations")])
    suite = testLoader.loadTestsFromTestCase(ListOfHwIOsSample4TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synth import to_rtl_str
    print(to_rtl_str(ListOfHwIOsSample4c()))
