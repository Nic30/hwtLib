#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.hdl.types.defs import INT
from hwt.hdl.types.bits import HBits


class ParametrizationExample(HwModule):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.PARAM_0 = HwParam(0)
        self.PARAM_10 = HwParam(10)
        try:
            self.PARAM_1_sll_512 = HwParam(INT.from_py(1 << 512))
            raise AssertionError("Parameter with int value which is"
                                 "too big to fit in integer type of target hdl language")
        except ValueError:
            # portable type for large int, generally int in verilog/vhdl is 32b wide
            self.PARAM_1_sll_512 = HwParam(HBits(512 + 1).from_py(1 << 512))
            self.PARAM_1_sll_512_py_int = HwParam(1 << 512)

    def _declr(self):
        assert int(self.PARAM_0) == 0
        assert int(self.PARAM_10 + 10) == 20
        assert int(self.PARAM_1_sll_512) == 1 << 512
        self.din = HwIOVectSignal(self.PARAM_10)
        self.dout = HwIOVectSignal(self.PARAM_10 * 2)._m()

    def _impl(self):
        assert int(self.PARAM_0) == 0
        assert int(self.PARAM_10 + 10) == 20
        assert int(self.PARAM_1_sll_512) == 1 << 512

        self.dout(Concat(self.din, self.din))


if __name__ == "__main__":  # alias python main function
    from hwt.synth import to_rtl_str
    
    m = ParametrizationExample()
    print(to_rtl_str(m))
