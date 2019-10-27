#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.param import Param
from hwt.interfaces.utils import addClkRstn
from hwt.interfaces.std import VectSignal
from hwt.code import Add
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.hObjList import HObjList


class PidController(Unit):
    """
    The PID Control block compares the input to the target
    and calculates an error. Based on this error, a output value is calculated
    that should result in a smaller error on the next iteration of the loop,
    assuming your parameters are tuned properly.

    u(k) = u(k-1) + a0*e(k) + a1*y(k) + a2*y(k-1) + a3*y(k-2)

    e(k): error in this step (= target value - input)
    y(k): input in step k
    ax: PID coeficient

    The PID parameter inputs for this equation are slightly different
    from the traditional K_p, K_i, and K_d.

    a0 = K_i * T_s
    a1 = -K_p - K_d / T_s
    a2 = K_p + 2K_d/T_s
    a3 = - K_d / T_s

    :note: You can obtain coeficiet f.e. by Ziegler-Nichols method.

    .. hwt-schematic::
    """

    def _config(self):
        self.DATAIN_WIDTH = Param(16)
        self.DATAOUT_WIDTH = Param(16)
        self.COEF_WIDTH = Param(16)

    def _declr(self):
        addClkRstn(self)
        self.input = VectSignal(self.DATAIN_WIDTH, signed=True)
        self.output = VectSignal(self.DATAIN_WIDTH, signed=True)._m()
        self.target = VectSignal(self.DATAIN_WIDTH, signed=True)
        self.coefs = HObjList(
            VectSignal(self.COEF_WIDTH, signed=True)
            for _ in range(4)
        )

    def _impl(self):
        u = self._reg("u", dtype=self.output._dtype, def_val=0)
        err = self._sig("err", dtype=self.input._dtype)
        err(self.input - self.target)

        # create y-pipeline
        y = [self.input, ]
        for i in range(2):
            _y = self._reg("y%d" % i, dtype=self.input._dtype, def_val=0)
            _y(y[-1])
            y.append(_y)

        a = self.coefs

        def trim(signal):
            return signal._reinterpret_cast(self.output._dtype)

        u(Add(u, a[0] * err, a[1] * y[0], a[2] * y[1], a[3] * y[2], key=trim))
        self.output(u)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(PidController()))
