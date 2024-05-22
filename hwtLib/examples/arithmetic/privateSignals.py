from hwt.hwModule import HwModule
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.utils import addClkRstn


class PrivateSignalsOfStructType(HwModule):

    def hwDeclr(self):
        addClkRstn(self)
        self.a = HwIOVectSignal(8)
        self.b = HwIOVectSignal(8)._m()

        self.c = HwIOVectSignal(8)
        self.d = HwIOVectSignal(8)._m()

    def hwImpl(self):
        t = self.a._dtype
        tmp_t = \
        HStruct(
            (t, "a0"),
            (t, "a1"),
            (t[2], "a2_3"),
            (HStruct(
                (t, "a4"),
                (t[2], "a5_6"),
                ),
                "a4_5_6"
            ),
        )
        tmp = self._sig("tmp", tmp_t)
        self.connect_tmp_chain(tmp, self.a, self.b)

        tmp_reg = self._reg("tmp_reg", tmp_t, def_val={
            "a0": 0,
            "a1": 1,
            "a2_3": [2, 3],
            "a4_5_6": {
                "a4": 4,
                "a5_6": [5, 6],
            }
        })
        self.connect_tmp_chain(tmp_reg, self.c, self.d)

    def connect_tmp_chain(self, tmp, a_in, a_out):
        # a connected to b using chain of tmp signals from tmp sig
        tmp.a0(a_in)
        tmp.a1(tmp.a0)
        tmp.a2_3[0](tmp.a1)
        tmp.a2_3[1](tmp.a2_3[0])
        tmp.a4_5_6.a4(tmp.a2_3[1])
        tmp.a4_5_6.a5_6[0](tmp.a4_5_6.a4)
        tmp.a4_5_6.a5_6[1](tmp.a4_5_6.a5_6[0])
        a_out(tmp.a4_5_6.a5_6[1])


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = PrivateSignalsOfStructType()
    print(to_rtl_str(m))
