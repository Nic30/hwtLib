#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple, Optional

from hwt.code import If
from hwt.constraints import set_max_delay, set_async_reg
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIORst, HwIOSignal, HwIOClk
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.mainBases import RtlSignalBase
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.interfaceLevel.hwModuleImplHelpers import getSignalName
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


class SignalCdcBuilder():
    """
    Object which can build CDCs for simple HwIOSignal interfaces.
    It automatically adding constrains and check correnctnes of CDC path.
    Main purpose of this class is to allow building
    of CDCs without requirement of component instantiation.
    """
    def __init__(self, sig,
                 in_clk_rst: Tuple[RtlSignal, RtlSignal],
                 out_clk_rst: Tuple[RtlSignal, RtlSignal],
                 reg_init_val, name_prefix: Optional[str]=None):
        """
        :param sig: data in signal
        :param in_clk_rst: tuple source clk signal, rst signal
        :param out_clk_rst: tuple destination clk signal, rst signal
        :note: rst/rst_n is automatically resolved from reset type
        :param reg_init_val: register reset value
        """
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
            return i._rtlCtx.parent
        else:
            # interface
            i = i._parent
            while not isinstance(i, HwModule):
                i = i._parent
            return i

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
        inReg = self._reg(f"{self.name_prefix:s}in_reg{self.in_reg_cnt:d}",
                          self.IN_CLK_RST)
        inReg(self.path[-1])
        self.path.append(inReg)
        self.in_reg_cnt += 1

    def add_out_reg(self, en: Optional[RtlSignal]=None):
        path = self.path
        outReg = self._reg(f"{self.name_prefix:s}out_reg{self.out_reg_cnt:d}",
                           self.OUT_CLK_RST)
        end = path[-1]
        if en is not None:
            If(en,
               outReg(end)
            )
        else:
            outReg(end)

        set_max_delay(end, outReg, self.META_PERIOD_NS)
        set_async_reg(outReg)
        path.append(outReg)
        self.out_reg_cnt += 1


class Cdc(HwModule):
    """
    CDC (Clock Domain Crossing) for HwIOSignal interface
    (Synchronizes the signal for different clock domain.)

    :attention: regular multibits signals should not be sychronized using
        this sychronizer instead handshake or req-ack sychronization
        should be used for control signals and main data should be
        passed over couple of registers

    :ivar ~.DATA_WIDTH: width of data-signal
    :ivar ~.INIT_VAL: initialization value for registers
    :ivar ~.IN_FREQ: frequency of clock signal for input data [Hz]
    :ivar ~.OUT_FREQ: frequency of clock signal for output data [Hz]
    :ivar ~.OUT_REG_CNT: number of registers for synchronization in dataOut clock domain

    .. hwt-autodoc::
    """
    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(1)
        self.INIT_VAL = HwParam(0)
        self.IN_FREQ = HwParam(100e6)
        self.OUT_FREQ = HwParam(100e6)
        self.OUT_REG_CNT = HwParam(2)

    @override
    def hwDeclr(self):
        assert self.OUT_REG_CNT >= 2, self.OUT_REG_CNT

        self.dataIn_clk = HwIOClk()
        self.dataIn_clk.FREQ = self.IN_FREQ
        with self._associated(clk=self.dataIn_clk):
            self.dataIn_rst = HwIORst()
            with self._associated(rst=self.dataIn_rst):
                self.dataIn = HwIOSignal(dtype=HBits(self.DATA_WIDTH))

        self.dataOut_clk = HwIOClk()
        self.dataOut_clk.FREQ = self.OUT_FREQ
        with self._associated(clk=self.dataOut_clk):
            self.dataOut_rst = HwIORst()
            with self._associated(rst=self.dataOut_rst):
                self.dataOut = HwIOSignal(dtype=HBits(self.DATA_WIDTH))._m()

    @override
    def hwImpl(self):
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
    .. code-block:: python

        if inData_clk.FREQ > outData_clk.FREQ:
            outData_clk.FREQ >= 1.5*inData_clk.FREQ
        else:
            inData_clk.FREQ >= 1.5*outData_clk.FREQ

    .. hwt-autodoc::
    """
    @override
    def hwConfig(self):
        Cdc.hwConfig(self)
        self.OUT_REG_CNT = 3

    @override
    def hwDeclr(self):
        assert self.DATA_WIDTH == 1, self.DATA_WIDTH
        Cdc.hwDeclr(self)
        with self._associated(clk=self.dataOut_clk, rst=self.dataOut_rst):
            self.dataOut_en = HwIOSignal()._m()

    @override
    def hwImpl(self):
        (_, _, _, out_reg1, out_reg2) = Cdc.hwImpl(self)
        self.dataOut_en(out_reg1 ^ out_reg2)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    print(to_rtl_str(Cdc()))
