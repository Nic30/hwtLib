from hwt.code import Concat
from hwt.interfaces.std import VectSignal
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.hdlObjects.typeShortcuts import vec


class ParametrizationExample(Unit):
    def _config(self):
        self.PARAM_0 = Param(0)
        self.PARAM_10 = Param(10)
        try:
            self.PARAM_1_sll_512 = Param(1 << 512)
            assert False, "Parameter with int value which is too big to fit in integer type of target hdl language"
        except TypeError:
            # portable type for large int, generally int in verilog/vhdl is 32b wide
            self.PARAM_1_sll_512 = Param(vec(1 << 512, width=512 + 1))

    def _declr(self):
        assert int(self.PARAM_0) == 0
        assert int(self.PARAM_10 + 10) == 20
        assert int(self.PARAM_1_sll_512) == 1 << 512
        self.din = VectSignal(self.PARAM_10)
        self.dout = VectSignal(self.PARAM_10 * 2)

    def _impl(self):
        assert int(self.PARAM_0) == 0
        assert int(self.PARAM_10 + 10) == 20
        assert int(self.PARAM_1_sll_512) == 1 << 512

        self.dout ** Concat(self.din, self.din)

if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it only when this script is running as main
    from hwt.synthesizer.shortcuts import toRtl
    # we create instance of our unit
    u = ParametrizationExample()
    # there is more of synthesis methods. toRtl() returns formated hdl string
    print(toRtl(u))
