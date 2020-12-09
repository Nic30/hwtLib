#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Type

from hwt.interfaces.std import Clk, Rst_n, VldSynced
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import packIntf, \
    connectPacked
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.clocking.cdc import SignalCdcBuilder


class VldSyncedCdc(Unit):
    """
    Clock Domain Crossing for VldSynced interfaces

    :attention: if the destination clock domain is slower,
        data may be dropped (and probably will be),
        by default there is an assert to prevent that,
        use IGNORE_DATA_LOSE to ignore it

    .. hwt-autodoc:: _example_VldSyncedCdc
    """

    def __init__(self, intfCls: Type[VldSynced]):
        """
        :param hsIntfCls: class of interface which should be used
            as interface of this unit
        """
        self.intfCls = intfCls
        Unit.__init__(self)

    @classmethod
    def get_valid_signal(cls, intf):
        return intf.vld

    def get_data(self, intf):
        vld = self.get_valid_signal(intf)
        return [x for x in intf._interfaces if x is not vld]

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.intfCls._config(self)
        self.DATA_RESET_VAL = Param(None)
        self.IN_FREQ = Param(int(100e6))
        self.OUT_FREQ = Param(int(100e6))
        self.IGNORE_DATA_LOSE = Param(False)

    def _declr(self):
        I_CLS = self.intfCls

        self.dataIn_clk = Clk()
        self.dataIn_clk.FREQ = self.IN_FREQ
        with self._associated(self.dataIn_clk):
            self.dataIn_rst_n = Rst_n()

        self.dataOut_clk = Clk()
        self.dataOut_clk.FREQ = self.OUT_FREQ
        with self._associated(self.dataOut_clk):
            self.dataOut_rst_n = Rst_n()

        with self._paramsShared():
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

        in_data = packIntf(self.dataIn, exclude=[in_vld])
        b_data = SignalCdcBuilder(
            in_data, in_clk_rst_n, out_clk_rst_n,
            self.DATA_RESET_VAL, name_prefix="")
        b_data.add_in_reg()
        b_data.add_out_reg(en=out_data_en)

        connectPacked(b_data.path[-1], self.dataOut, exclude=[out_vld])

def _example_VldSyncedCdc():
    return VldSyncedCdc(VldSynced)

if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_VldSyncedCdc()
    print(to_rtl_str(u))
