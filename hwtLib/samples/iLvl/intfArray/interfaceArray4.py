from hwt.code import log2ceil
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.std import RegCntrl, BramPort_withoutClk
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam
from hwtLib.types.ctypes import uint32_t


struct0 = HStruct(
        (uint32_t, "f0"),
        (Array(
               HStruct((uint32_t, "f1"), (uint32_t, "f2")),
               4), "arr0")
    )

class InterfaceArraySample4(Unit):
    @staticmethod
    def shouldEnterFn(field):
        return False

    def _mkFieldInterface(self, field):
        t = field.dtype

        if isinstance(t, Bits):
            p = RegCntrl()
            dw = t.bit_length()
        elif isinstance(t, Array):
            if self.shouldEnterFn(field):
                p = StructIntf(t.elmType, instantiateFieldFn=self._mkFieldInterface, multipliedBy=t.size)
                return p
            else:
                p = BramPort_withoutClk()
                dw = t.elmType.bit_length()
                p.ADDR_WIDTH.set(log2ceil(evalParam(t.size).val - 1))
        else:
            raise NotImplementedError(t)

        p.DATA_WIDTH.set(dw)

        return p

    def _declr(self):
        addClkRstn(self)
        self.a = StructIntf(struct0, instantiateFieldFn=self._mkFieldInterface, multipliedBy=3)
        self.b = StructIntf(struct0, instantiateFieldFn=self._mkFieldInterface, multipliedBy=3)
    
    def _impl(self):
        self.b ** self.a
        
        
class InterfaceArraySample4b(InterfaceArraySample4):    
    @staticmethod
    def shouldEnterFn(field):
        return True

class InterfaceArraySample4TC(SimTestCase):

    def test_InterfaceArraySample4b(self):
        u = InterfaceArraySample4b()
        self.prepareUnit(u)

        r = self._rand.getrandbits
        def randInts():
            return [r(32) for _ in range(r(2))]

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
            b.f0._ag.dout.extend(_f0_in)
            f0_in.append(_f0_in)
            f0_out.append(_f0_out)
            
            arr_f1_in = []
            arr_f2_in = []
            arr_f1_out = []
            arr_f2_out = []            
            for i2 in range(4):
                _a = a.arr0[i2]
                _b = b.arr0[i2]  
                _f1_in = randInts()
                _f2_in = randInts()
                _f1_out = randInts()
                _f2_out = randInts()
                
                _a.f1._ag.dout.extend(_f1_out)
                _a.f2._ag.dout.extend(_f2_out)
                _b.f1._ag.dout.extend(_f1_in)
                _b.f2._ag.dout.extend(_f2_in)

                arr_f1_out.append(_f1_out)
                arr_f1_in.append(_f1_in)
                arr_f2_out.append(_f2_out)
                arr_f2_in.append(_f2_in)


            f1_out.append(arr_f1_out)
            f1_in.append(arr_f1_in)
            f2_out.append(arr_f2_out)
            f2_in.append(arr_f2_in)


        self.doSim(100 * Time.ns)

        emp = self.assertEmpty
        eq = self.assertValSequenceEqual
        for _f0_in, _f0_out, arr_f1_in, arr_f1_out, arr_f2_in, arr_f2_out in zip(f0_in, f0_out, f1_in, f1_out, f2_in, f2_out):
            a = u.a[i]
            b = u.b[i]
            
            emp(a.f0._ag.dout)
            eq(a.f0._ag.din, _f0_in)
            emp(b.f0._ag.dout)
            eq(b.f0._ag.din, _f0_out)

            for _f1_in, _f1_out, _f2_in, _f2_out in zip(arr_f1_in, arr_f1_out, arr_f2_in, arr_f2_out):
                a = a.arr0[i2]
                b = b.arr0[i2]  
                
                emp(a.f1._ag.dout)
                emp(a.f2._ag.dout)
                emp(b.f1._ag.dout)
                emp(b.f2._ag.dout)




if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(InterfaceArraySample3TC('test_simplePass'))
    suite.addTest(unittest.makeSuite(InterfaceArraySample4TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    
    # from hwt.synthesizer.shortcuts import toRtl
    # print(toRtl(InterfaceArraySample4()))