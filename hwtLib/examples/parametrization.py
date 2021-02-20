#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.interfaces.std import VectSignal
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.hdl.types.defs import INT
from hwt.hdl.types.bits import Bits


class ParametrizationExample(Unit):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.PARAM_0 = Param(0)
        self.PARAM_10 = Param(10)
        try:
            self.PARAM_1_sll_512 = Param(INT.from_py(1 << 512))
            raise AssertionError("Parameter with int value which is"
                                 "too big to fit in integer type of target hdl language")
        except ValueError:
            # portable type for large int, generally int in verilog/vhdl is 32b wide
            self.PARAM_1_sll_512 = Param(Bits(512 + 1).from_py(1 << 512))
            self.PARAM_1_sll_512_py_int = Param(1 << 512)

    def _declr(self):
        assert int(self.PARAM_0) == 0
        assert int(self.PARAM_10 + 10) == 20
        assert int(self.PARAM_1_sll_512) == 1 << 512
        self.din = VectSignal(self.PARAM_10)
        self.dout = VectSignal(self.PARAM_10 * 2)._m()

    def _impl(self):
        assert int(self.PARAM_0) == 0
        assert int(self.PARAM_10 + 10) == 20
        assert int(self.PARAM_1_sll_512) == 1 << 512

        self.dout(Concat(self.din, self.din))


if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.utils import to_rtl_str
    u = ParametrizationExample()
    print(to_rtl_str(u))
