#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple, Optional

from hwt.constraints import set_max_delay, set_async_reg
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Rst, Signal, Clk
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName


class SignalCdcBuilder():
    """
    Object which can build CDCs fro simple Signal interfaces
    It automatically adding constrains and check correnctne of CDC path
    But main purpose of this class is to allow building
    of CDCs without requirement of component instantiation
    """
    def __init__(self, sig,
                 in_clk_rst: Tuple[RtlSignal, RtlSignal],
                 out_clk_rst: Tuple[RtlSignal, RtlSignal],
                 reg_init_val, name_prefix: Optional[str]=None):
        self.path = [sig, ]
        if name_prefix is None:
            name_prefix = getSignalName(sig) + "_"
        self.name_prefix = name_prefix
        self.IN_CLK_RST = in_clk_rst
        self.OUT_CLK_RST = out_clk_rst
        self.REG_INIT_VAL = reg_init_val
        self.META_PERIOD_NS =\
            1e9 / max(in_clk_rst[0].FREQ, in_clk_rst[0].FREQ) * 0.5
        self.in_reg_cnt = 0
        self.out_reg_cnt = 0

    def _parent(self):
        i = self.path[0]
        if isinstance(i, RtlSignalBase):
            return i.ctx.parent
        else:
            return i._parent

    def _reg(self, name, clk_rst):
        clk, rst = clk_rst
        din = self.path[-1]
        return self._parent()._reg(
            name,
            din._dtype,
            clk=clk,
            rst=rst,
            def_val=self.REG_INIT_VAL)

    def add_in_reg(self):
        assert self.out_reg_cnt == 0, self.out_reg_cnt
        inReg = self._reg(self.name_prefix + "in_reg%d" % self.out_reg_cnt,
                          self.IN_CLK_RST)
        inReg(self.path[-1])
        self.path.append(inReg)
        self.in_reg_cnt += 1

    def add_out_reg(self):
        path = self.path
        outReg = self._reg(self.name_prefix + "out_reg%d" % self.out_reg_cnt,
                           self.OUT_CLK_RST)
        outReg(path[-1])
        set_max_delay(path[-1], outReg, self.META_PERIOD_NS)
        set_async_reg(outReg)
        path.append(outReg)
        self.out_reg_cnt += 1


class Cdc(Unit):
    """
    CDC (Clock Domain Crossing) for Signal interface
    (Synchronizes the signal for different clock domain.)

    :attention: regular multibits signals should not be sychronized using
        this sychronizer instead handshake or req-ack sychronization
        should be used for controll signals and main data should be
        passed over couple of registers

    :ivar DATA_WIDTH: width of data-signal
    :ivar INIT_VAL: initialization value for registers
    :ivar IN_FREQ: frequency of clock signal for input data [Hz]
    :ivar OUT_FREQ: frequency of clock signal for output data [Hz]
    :ivar OUT_REG_CNT: number of registers for synchronization in dataOut clock domain

    .. hwt-schematic::
    """
    def _config(self):
        self.DATA_WIDTH = Param(1)
        self.INIT_VAL = Param(0)
        self.IN_FREQ = Param(100e6)
        self.OUT_FREQ = Param(100e6)
        self.OUT_REG_CNT = Param(2)

    def _declr(self):
        assert self.OUT_REG_CNT >= 2, self.OUT_REG_CNT

        self.dataIn_clk = Clk()
        self.dataIn_clk.FREQ = self.IN_FREQ
        with self._associated(clk=self.dataIn_clk):
            self.dataIn_rst = Rst()
            with self._associated(rst=self.dataIn_rst):
                self.dataIn = Signal(dtype=Bits(self.DATA_WIDTH))

        self.dataOut_clk = Clk()
        self.dataOut_clk.FREQ = self.OUT_FREQ
        with self._associated(clk=self.dataOut_clk):
            self.dataOut_rst = Rst()
            with self._associated(rst=self.dataOut_rst):
                self.dataOut = Signal(dtype=Bits(self.DATA_WIDTH))._m()

    def _impl(self):
        in_clk_rst = self.dataIn_clk, self.dataIn_rst
        out_clk_rst = self.dataOut_clk, self.dataOut_rst

        b = SignalCdcBuilder(
            self.dataIn, in_clk_rst, out_clk_rst,
            self.INIT_VAL, name_prefix="")
        b.add_in_reg()
        for _ in range(self.OUT_REG_CNT):
            b.add_out_reg()
        self.dataOut(b.path[-1])

        return b.path


class CdcPulseGen(Cdc):
    """
    If inData_clk.FREQ > outData_clk.FREQ:
        outData_clk.FREQ >= 1.5*inData_clk.FREQ
    else:
        inData_clk.FREQ >= 1.5*outData_clk.FREQ

    .. hwt-schematic::
    """
    def _config(self):
        Cdc._config(self)
        self.OUT_REG_CNT = 3

    def _declr(self):
        assert self.DATA_WIDTH == 1, self.DATA_WIDTH
        Cdc._declr(self)
        with self._associated(clk=self.dataOut_clk, rst=self.dataOut_rst):
            self.dataOut_en = Signal()._m()

    def _impl(self):
        (_, _, _, out_reg1, out_reg2) = Cdc._impl(self)
        self.dataOut_en(out_reg1 ^ out_reg2)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(Cdc()))
