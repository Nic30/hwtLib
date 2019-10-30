from hwt.code import log2ceil
from hwt.hdl.constants import Time
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import RegCntrl, BramPort_withoutClk
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.unit import Unit

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


class ListOfInterfacesSample4(Unit):
    """
    Example with HObjList of interfaces where interfaces are instances of StructIntf
    which is interface dynamically generated from c-like structure description

    .. hwt-schematic::
    """

    @staticmethod
    def shouldEnterFn(field):
        return False, True

    def _mkFieldInterface(self, structIntf, field):
        t = field.dtype

        if isinstance(t, Bits):
            p = RegCntrl()
            dw = t.bit_length()
        elif isinstance(t, HArray):
            if self.shouldEnterFn(field):
                if isinstance(t.element_t, Bits):
                    p = HObjList(RegCntrl() for _ in range(int(t.size)))
                    dw = t.element_t.bit_length()
                else:
                    p = HObjList([StructIntf(
                        t.element_t,
                        instantiateFieldFn=self._mkFieldInterface)
                        for _ in range(int(t.size))])
                    return p
            else:
                p = BramPort_withoutClk()
                dw = t.element_t.bit_length()
                p.ADDR_WIDTH = log2ceil(int(t.size) - 1)
        else:
            raise NotImplementedError(t)

        p.DATA_WIDTH = dw

        return p

    def _declr(self):
        addClkRstn(self)
        self.a = HObjList(
            StructIntf(
                struct0,
                instantiateFieldFn=self._mkFieldInterface)
            for _ in range(3))
        self.b = HObjList(
            StructIntf(
                struct0,
                instantiateFieldFn=self._mkFieldInterface)
            for _ in range(3))._m()

    def _impl(self):
        self.b(self.a)


class ListOfInterfacesSample4b(ListOfInterfacesSample4):
    """
    .. hwt-schematic::
    """
    @staticmethod
    def shouldEnterFn(field):
        return True, True


class ListOfInterfacesSample4c(ListOfInterfacesSample4b):
    """
    .. hwt-schematic::
    """
    def _impl(self):
        for a, b in zip(self.a, self.b):
            b(a)


class ListOfInterfacesSample4d(ListOfInterfacesSample4b):
    """
    .. hwt-schematic::
    """
    def _impl(self):
        for a, b in zip(self.a, self.b):
            b.f0(a.f0)
            for a_arr, b_arr in zip(a.arr0, b.arr0):
                b_arr(a_arr)


class ListOfInterfacesSample4TC(SimTestCase):

    def test_ListOfInterfacesSample4b_intfIterations(self):
        u = ListOfInterfacesSample4d()
        self.compileSimAndStart(u)

        i = 0
        for a in u.a:
            for _ in a.arr0:
                i += 1
        self.assertValEqual(i, 3*4)

        i = 0
        for intf in u.a:
            i += 1
            a = 0
            for _ in intf.arr0:
                a += 1
            self.assertValEqual(a, 4)

        self.assertValEqual(i, 3)

    def _test(self, u):
        self.compileSimAndStart(u)
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
            a = u.a[i]
            b = u.b[i]
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
                f2_out, u.a, u.b)):

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

    def test_ListOfInterfacesSample4b(self):
        u = ListOfInterfacesSample4b()
        self._test(u)

    def test_ListOfInterfacesSample4c(self):
        u = ListOfInterfacesSample4c()
        self._test(u)

    def test_ListOfInterfacesSample4d(self):
        u = ListOfInterfacesSample4d()
        self._test(u)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    #suite.addTest(ListOfInterfacesSample4TC('test_ListOfInterfacesSample4b_intfIterations'))
    # suite.addTest(ListOfInterfacesSample4TC('test_ListOfInterfacesSample4b'))

    suite.addTest(unittest.makeSuite(ListOfInterfacesSample4TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synthesizer.utils import toRtl
    print(toRtl(ListOfInterfacesSample4c()))
