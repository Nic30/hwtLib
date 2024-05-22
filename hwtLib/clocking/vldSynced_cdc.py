#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Type

from hwt.hwIOs.std import HwIOClk, HwIORst_n, HwIODataVld
from hwt.synthesizer.interfaceLevel.utils import HwIO_pack, \
    HwIO_connectPacked
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwtLib.clocking.cdc import SignalCdcBuilder


class VldSyncedCdc(HwModule):
    """
    Clock Domain Crossing for HwIODataVld interfaces

    :attention: if the destination clock domain is slower,
        data may be dropped (and probably will be),
        by default there is an assert to prevent that,
        use IGNORE_DATA_LOSE to ignore it

    .. hwt-autodoc:: _example_VldSyncedCdc
    """

    def __init__(self, hwIOCls: Type[HwIODataVld]):
        """
        :param hshwIO: class of interface which should be used
            as interface of this unit
        """
        self.hwIOCls = hwIOCls
        HwModule.__init__(self)

    @classmethod
    def get_valid_signal(cls, hwIO):
        return hwIO.vld

    def get_data(self, hwIO):
        vld = self.get_valid_signal(hwIO)
        return [hwIO for hwIO in hwIO._hwIOs if hwIO is not vld]

    def _config(self):
        self.HWIO_CLS = HwParam(self.hwIOCls)
        self.hwIOCls._config(self)
        self.DATA_RESET_VAL = HwParam(None)
        self.IN_FREQ = HwParam(int(100e6))
        self.OUT_FREQ = HwParam(int(100e6))
        self.IGNORE_DATA_LOSE = HwParam(False)

    def _declr(self):
        I_CLS = self.hwIOCls

        self.dataIn_clk = HwIOClk()
        self.dataIn_clk.FREQ = self.IN_FREQ
        with self._associated(self.dataIn_clk):
            self.dataIn_rst_n = HwIORst_n()

        self.dataOut_clk = HwIOClk()
        self.dataOut_clk.FREQ = self.OUT_FREQ
        with self._associated(self.dataOut_clk):
            self.dataOut_rst_n = HwIORst_n()

        with self._hwParamsShared():
            with self._associated(self.dataIn_clk, self.dataIn_rst_n):
                self.dataIn = I_CLS()
            with self._associated(self.dataOut_clk, self.dataOut_rst_n):
                self.dataOut = I_CLS()._m()

    def _impl(self):
        if not self.IGNORE_DATA_LOSE:
            assert self.IN_FREQ <= self.OUT_FREQ
        in_clk_rst_n = self.dataIn_clk, self.dataIn_rst_n
        out_clk_rst_n = self.dataOut_clk, self.dataOut_rst_n
        in_vld, out_vld = (
            self.get_valid_signal(self.dataIn),
            self.get_valid_signal(self.dataOut)
        )

        b_cntrl = SignalCdcBuilder(
            in_vld, in_clk_rst_n, out_clk_rst_n,
            0, name_prefix="")
        b_cntrl.add_in_reg()
        for _ in range(3):
            b_cntrl.add_out_reg()
        out_data_en = b_cntrl.path[-2]
        out_vld(b_cntrl.path[-1])

        in_data = HwIO_pack(self.dataIn, exclude=[in_vld])
        b_data = SignalCdcBuilder(
            in_data, in_clk_rst_n, out_clk_rst_n,
            self.DATA_RESET_VAL, name_prefix="")
        b_data.add_in_reg()
        b_data.add_out_reg(en=out_data_en)

        HwIO_connectPacked(b_data.path[-1], self.dataOut, exclude=[out_vld])

def _example_VldSyncedCdc():
    return VldSyncedCdc(HwIODataVld)

if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_VldSyncedCdc()
    print(to_rtl_str(m))
