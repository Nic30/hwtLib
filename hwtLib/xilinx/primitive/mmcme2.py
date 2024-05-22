#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT, BOOL, STR
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeExclude
from hwt.serializer.verilog import VerilogSerializer
from hwtLib.xilinx.platform import XilinxVivadoPlatform
from ipCorePackager.constants import INTF_DIRECTION


@serializeExclude
class MMCME2_ADV(HwModule):
    """
    Mixed-Mode Clock Manager (PLL like frequency synchronizer/clock generator) on Xilinx 7+ series

    https://www.xilinx.com/support/documentation/user_guides/ug472_7Series_Clocking.pdf
    """

    @override
    def hwConfig(self):
        self.BANDWIDTH = HwParam("OPTIMIZED")
        self.CLKFBOUT_MULT_F = HwParam(5.0)
        self.CLKFBOUT_PHASE = HwParam(0.0)
        self.CLKFBOUT_USE_FINE_PS = HwParam(False)
        self.CLKIN1_PERIOD = HwParam(0.0)
        self.CLKIN2_PERIOD = HwParam(0.0)

        self.CLKOUT0_DIVIDE_F = HwParam(1.0)
        self.CLKOUT0_DUTY_CYCLE = HwParam(0.5)
        self.CLKOUT0_PHASE = HwParam(0.0)
        self.CLKOUT0_USE_FINE_PS = HwParam(False)

        self.CLKOUT1_DIVIDE = HwParam(1)
        self.CLKOUT1_DUTY_CYCLE = HwParam(0.5)
        self.CLKOUT1_PHASE = HwParam(0.0)
        self.CLKOUT1_USE_FINE_PS = HwParam(False)

        self.CLKOUT2_DIVIDE = HwParam(1)
        self.CLKOUT2_DUTY_CYCLE = HwParam(0.5)
        self.CLKOUT2_PHASE = HwParam(0.0)
        self.CLKOUT2_USE_FINE_PS = HwParam(False)

        self.CLKOUT3_DIVIDE = HwParam(1)
        self.CLKOUT3_DUTY_CYCLE = HwParam(0.5)
        self.CLKOUT3_PHASE = HwParam(0.0)
        self.CLKOUT3_USE_FINE_PS = HwParam(False)

        self.CLKOUT4_CASCADE = HwParam(False)
        self.CLKOUT4_DIVIDE = HwParam(1)
        self.CLKOUT4_DUTY_CYCLE = HwParam(0.5)
        self.CLKOUT4_PHASE = HwParam(0.0)
        self.CLKOUT4_USE_FINE_PS = HwParam(False)

        self.CLKOUT5_DIVIDE = HwParam(1)
        self.CLKOUT5_DUTY_CYCLE = HwParam(0.5)
        self.CLKOUT5_PHASE = HwParam(0.0)
        self.CLKOUT5_USE_FINE_PS = HwParam(False)

        self.CLKOUT6_DIVIDE = HwParam(1)
        self.CLKOUT6_DUTY_CYCLE = HwParam(0.5)
        self.CLKOUT6_PHASE = HwParam(0.0)
        self.CLKOUT6_USE_FINE_PS = HwParam(False)

        self.COMPENSATION = HwParam("ZHOLD")
        self.DIVCLK_DIVIDE = HwParam(1)
        self.IS_CLKINSEL_INVERTED = HwParam(BIT.from_py(0b0))
        self.IS_PSEN_INVERTED = HwParam(BIT.from_py(0b0))
        self.IS_PSINCDEC_INVERTED = HwParam(BIT.from_py(0b0))
        self.IS_PWRDWN_INVERTED = HwParam(BIT.from_py(0b0))
        self.IS_RST_INVERTED = HwParam(BIT.from_py(0b0))
        self.REF_JITTER1 = HwParam(0.01)
        self.REF_JITTER2 = HwParam(0.01)
        self.SS_EN = HwParam(False)
        self.SS_MOD_PERIOD = HwParam(10000)
        self.SS_MODE = HwParam("CENTER_HIGH")
        self.STARTUP_WAIT = HwParam(False)

    def clkout_duty_chk(self, CLKOUT_DIVIDE, CLKOUT_DUTY_CYCLE, CLKOUT_DUTY_CYCLE_N):
        O_MAX_HT_LT = 64

        if CLKOUT_DIVIDE > O_MAX_HT_LT:
            CLK_DUTY_CYCLE_MIN = 1.0 * (CLKOUT_DIVIDE - O_MAX_HT_LT) / CLKOUT_DIVIDE
            CLK_DUTY_CYCLE_MAX = (O_MAX_HT_LT + 0.5) / CLKOUT_DIVIDE
            CLK_DUTY_CYCLE_MIN_rnd = CLK_DUTY_CYCLE_MIN
        else:
            if CLKOUT_DIVIDE == 1.0:
                CLK_DUTY_CYCLE_MIN = 0.0
                CLK_DUTY_CYCLE_MIN_rnd = 0.0
            else:
                step_tmp = 1000 / CLKOUT_DIVIDE
                CLK_DUTY_CYCLE_MIN_rnd = step_tmp / 1000.0
                CLK_DUTY_CYCLE_MIN = 1.0 / CLKOUT_DIVIDE

            CLK_DUTY_CYCLE_MAX = 1.0

        if (CLKOUT_DUTY_CYCLE > CLK_DUTY_CYCLE_MAX) | (CLKOUT_DUTY_CYCLE < CLK_DUTY_CYCLE_MIN_rnd):
            raise AssertionError(
                "%s is set to %f on instance %m and is not in the allowed range %f to %f.",
                  CLKOUT_DUTY_CYCLE_N, CLKOUT_DUTY_CYCLE, CLK_DUTY_CYCLE_MIN, CLK_DUTY_CYCLE_MAX)

    def param_range_chk(self, para_in, para_name, range_low, range_high):
        if (para_in < range_low) or (para_in > range_high):
            raise AssertionError(
                "The %s set to %d. Legal values for this attribute are %d to %d.",
                para_name, para_in, range_low, range_high)

    def type_check_bool_param(self, name):
        STR_BOOL = ("TRUE", "FALSE")
        v = getattr(self, name)
        if self._store_manager.serializer_cls == VerilogSerializer:
            # for verilog we need to convert it to  "TRUE" or "FALSE" string
            if not isinstance(v, STR.getConstCls()):
                if isinstance(v, (bool, BIT.getConstCls())):
                    v = "TRUE" if v else "FALSE"
                else:
                    assert v in STR_BOOL, (name, v)
                v = STR.from_py(v)
                object.__setattr__(self, name, v)
            else:
                assert v._dtype == STR, (name, "must be of type ", STR, " or compatible, is:", v)
        else:
            if not isinstance(v, BOOL.getConstCls()):
                if isinstance(v, (str, STR.getConstCls())):
                    v = str(v)
                    if v == "FALSE":
                        v = False
                    elif v == "TRUE":
                        v = True
                    else:
                        raise AssertionError(name, "must be of type ", BOOL, " or string \"TRUE\" or \"FALSE\" or compatible, is:", v)

                v = BOOL.from_py(v)
                object.__setattr__(self, name, v)
            else:
                assert v._dtype == BOOL, (name, "must be of type ", BOOL, " or compatible, is:", v)

    def type_check_bit_param(self, name):
        v = getattr(self, name)
        if not isinstance(v, BIT.getConstCls()):
            v = BIT.from_py(v)
            object.__setattr__(self, name, v)
        else:
            assert v._dtype == BIT, (name, "must be of type ", BIT, " or compatible, is:", v)

    @override
    def hwDeclr(self):
        self.CLKFBIN = HwIOSignal()
        self.CLKFBOUT = HwIOSignal()._m()
        self.CLKFBOUTB = HwIOSignal()._m()
        self.CLKFBSTOPPED = HwIOSignal()._m()

        self.CLKIN1 = HwIOSignal()
        self.CLKIN2 = HwIOSignal()
        self.CLKINSEL = HwIOSignal()
        self.CLKINSTOPPED = HwIOSignal()._m()

        # B variant of clock is inverted clock
        self.CLKOUT0 = HwIOSignal()._m()
        self.CLKOUT0B = HwIOSignal()._m()
        self.CLKOUT1 = HwIOSignal()._m()
        self.CLKOUT1B = HwIOSignal()._m()
        self.CLKOUT2 = HwIOSignal()._m()
        self.CLKOUT2B = HwIOSignal()._m()
        self.CLKOUT3 = HwIOSignal()._m()
        self.CLKOUT3B = HwIOSignal()._m()
        self.CLKOUT4 = HwIOSignal()._m()
        self.CLKOUT5 = HwIOSignal()._m()
        self.CLKOUT6 = HwIOSignal()._m()

        # dynamic reconfig
        self.DADDR = HwIOSignal(HBits(7))
        self.DCLK = HwIOSignal()
        self.DEN = HwIOSignal()
        self.DI = HwIOSignal(HBits(16))
        self.DO = HwIOSignal(HBits(16))._m()
        self.DRDY = HwIOSignal()._m()
        self.DWE = HwIOSignal()

        self.LOCKED = HwIOSignal()._m()

        # phase shift control
        self.PSCLK = HwIOSignal()
        self.PSDONE = HwIOSignal()._m()
        self.PSEN = HwIOSignal()
        self.PSINCDEC = HwIOSignal()

        self.PWRDWN = HwIOSignal()
        self.RST = HwIOSignal()

        for name in ("IS_CLKINSEL_INVERTED", "IS_PSEN_INVERTED", "IS_PSINCDEC_INVERTED", "IS_PWRDWN_INVERTED", "IS_RST_INVERTED"):
            self.type_check_bit_param(name)

        for name in ["CLKFBOUT_USE_FINE_PS", "CLKOUT4_CASCADE", *(f'CLKOUT{i:d}_USE_FINE_PS' for i in range(7)), "STARTUP_WAIT"]:
            self.type_check_bool_param(name)

        assert self.BANDWIDTH in ("OPTIMIZED", "HIGH", "LOW"), self.BANDWIDTH
        assert self.COMPENSATION in ("ZHOLD", "BUF_IN", "EXTERNAL", "INTERNAL"), self.COMPENSATION
        assert self.SS_MODE in ("CENTER_HIGH", "CENTER_LOW", "DOWN_HIGH", "DOWN_LOW"), self.SS_MODE
        assert 4000 <= self.SS_MOD_PERIOD and self.SS_MOD_PERIOD <= 40000, self.SS_MOD_PERIOD

        clk0_div_fint = int(self.CLKOUT0_DIVIDE_F)
        clk0_div_frac = self.CLKOUT0_DIVIDE_F - clk0_div_fint
        clk0_frac_en = (clk0_div_frac > 0.0) and (clk0_div_fint >= 2)

        self.param_range_chk(self.CLKOUT0_DIVIDE_F, "CLKOUT0_DIVIDE_F", 1.0, 128.0)
        if (self.CLKOUT0_DIVIDE_F > 1.0) and (self.CLKOUT0_DIVIDE_F < 2.0):
            raise AssertionError("The Attribute CLKOUT0_DIVIDE_F set to %f.  Values in range of greater than 1 and less than 2 are not allowed.", self.CLKOUT0_DIVIDE_F)

        self.param_range_chk(self.CLKOUT0_PHASE, "CLKOUT0_PHASE", -360.0, 360.0)
        if not clk0_frac_en:
            self.param_range_chk(self.CLKOUT0_DUTY_CYCLE, "CLKOUT0_DUTY_CYCLE", 0.001, 0.999)
        elif self.CLKOUT0_DUTY_CYCLE != 0.5:
            raise AssertionError("CLKOUT0_DUTY_CYCLE set to %f. "
                                 " This attribute should be set to 0.5 when CLKOUT0_DIVIDE_F has fraction part.", self.CLKOUT0_DUTY_CYCLE)
        if not clk0_frac_en:
            self.clkout_duty_chk(self.CLKOUT0_DIVIDE_F, self.CLKOUT0_DUTY_CYCLE, "CLKOUT0_DUTY_CYCLE")

        for i in range(1, 6 + 1):
            CLKOUT_DIVIDE = getattr(self, f"CLKOUT{i:d}_DIVIDE")
            CLKOUT_PHASE = getattr(self, f"CLKOUT{i:d}_PHASE")
            CLKOUT_DUTY_CYCLE = getattr(self, f"CLKOUT{i:d}_DUTY_CYCLE")
            self.param_range_chk(CLKOUT_DIVIDE, f"CLKOUT{i:d}_DIVIDE", 1, 128)
            self.param_range_chk(CLKOUT_PHASE, f"CLKOUT{i:d}_PHASE", -360.0, 360.0)
            self.param_range_chk(CLKOUT_DUTY_CYCLE, f"CLKOUT{i:d}_DUTY_CYCLE", 0.001, 0.999)
            self.clkout_duty_chk(CLKOUT_DIVIDE, CLKOUT_DUTY_CYCLE, f"CLKOUT{i:d}_DUTY_CYCLE")

        VCOCLK_FREQ_MAX = 1600.0
        VCOCLK_FREQ_MIN = 600.0
        CLKIN_FREQ_MAX = 1066.0
        CLKIN_FREQ_MIN = 10.0
        # CLKPFD_FREQ_MAX = 550.0
        # CLKPFD_FREQ_MIN = 10.0
        # VCOCLK_FREQ_TARGET = 1000
        D_MIN = 1
        D_MAX = 106
        # O_MIN = 1
        # O_MAX = 128
        # REF_CLK_JITTER_MAX = 1000
        # REF_CLK_JITTER_SCALE = 0.100000
        # MAX_FEEDBACK_DELAY = 10.0
        # MAX_FEEDBACK_DELAY_SCALE = 1.0

        self.param_range_chk(self.CLKFBOUT_MULT_F, "CLKFBOUT_MULT_F", 2.0, 64.0)
        self.param_range_chk(self.CLKFBOUT_PHASE, "CLKFBOUT_PHASE", -360.0, 360.0)
        self.param_range_chk(self.DIVCLK_DIVIDE, "DIVCLK_DIVIDE", D_MIN, D_MAX)
        self.param_range_chk(self.REF_JITTER1, "REF_JITTER1", 0.0, 0.999)
        self.param_range_chk(self.REF_JITTER2, "REF_JITTER2", 0.0, 0.999)
        self.param_range_chk(self.DIVCLK_DIVIDE, "DIVCLK_DIVIDE", D_MIN, D_MAX)

        # raise AssertionError("Input Error : Input clock can only be switched when RST=1. CLKINSEL at time %t changed when RST low, which should change at RST high.", sim.now),
        clkin_chk_t1 = 0.001 * int(1000.0 * (1000.0 / CLKIN_FREQ_MIN))
        clkin_chk_t2 = 0.001 * int(1000.0 * (1000.0 / CLKIN_FREQ_MAX))
        CLKIN1_PERIOD = self.CLKIN1_PERIOD
        CLKIN2_PERIOD = self.CLKIN2_PERIOD

        if CLKIN1_PERIOD > clkin_chk_t1 or CLKIN1_PERIOD < clkin_chk_t2:
            raise AssertionError("The CLKIN1_PERIOD is set to %f ns and out the allowed range %f ns to %f ns.", CLKIN1_PERIOD, clkin_chk_t2, clkin_chk_t1)
        if CLKIN2_PERIOD != 0.0 and (CLKIN2_PERIOD > clkin_chk_t1 or CLKIN2_PERIOD < clkin_chk_t2):
            raise AssertionError("The CLKIN2_PERIOD is set to %f ns and out the allowed range %f ns to %f ns.", CLKIN2_PERIOD, clkin_chk_t2, clkin_chk_t1)

        assert (CLKIN1_PERIOD, CLKIN2_PERIOD) != (0.0, 0.0)
        for period_clkin in (CLKIN1_PERIOD, CLKIN2_PERIOD):
            if period_clkin == 0.0:
                continue
            clkvco_freq_init_chk = 1000.0 * self.CLKFBOUT_MULT_F / (period_clkin * self.DIVCLK_DIVIDE)
            if (clkvco_freq_init_chk > VCOCLK_FREQ_MAX) or (clkvco_freq_init_chk < VCOCLK_FREQ_MIN):
                    raise AssertionError(
                        "The calculation of VCO frequency=%f Mhz. This exceeds the permitted VCO frequency range of %f Mhz to %f Mhz."
                        " The VCO frequency is calculated with formula: VCO frequency =  CLKFBOUT_MULT_F / (DIVCLK_DIVIDE * CLKIN_PERIOD)."
                        " Please adjust the attributes to the permitted VCO frequency range.",
                        clkvco_freq_init_chk, VCOCLK_FREQ_MIN, VCOCLK_FREQ_MAX)

        assert isinstance(self._target_platform, XilinxVivadoPlatform), (self._target_platform, "This component is a hardblock of Xilinx devices only")

    @override
    def hwImpl(self):
        for hwIO in self._hwIOs:
            if hwIO._direction == INTF_DIRECTION.SLAVE:
                hwIO(None)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = MMCME2_ADV()
    m.BANDWIDTH = "OPTIMIZED"
    m.CLKFBOUT_MULT_F = 10.0
    m.CLKFBOUT_PHASE = 0.0
    m.CLKFBOUT_USE_FINE_PS = False
    m.CLKIN1_PERIOD = 10.0
    m.CLKIN2_PERIOD = 0.0
    m.CLKOUT0_DIVIDE_F = 10.0
    m.CLKOUT0_DUTY_CYCLE = 0.5
    m.CLKOUT0_PHASE = 0.0
    m.CLKOUT0_USE_FINE_PS = False
    for i in range(1, 6 + 1):
        setattr(m, f"CLKOUT{i:d}_DIVIDE", 1)
        setattr(m, f"CLKOUT{i:d}_DUTY_CYCLE", 0.5)
        setattr(m, f"CLKOUT{i:d}_PHASE", 0.0)
        setattr(m, f"CLKOUT{i:d}_USE_FINE_PS", False)
    m.CLKOUT4_CASCADE = False

    m.COMPENSATION = "ZHOLD"
    m.DIVCLK_DIVIDE = 1
    m.IS_CLKINSEL_INVERTED = BIT.from_py(0)
    m.IS_PSEN_INVERTED = BIT.from_py(0)
    m.IS_PSINCDEC_INVERTED = BIT.from_py(0)
    m.IS_PWRDWN_INVERTED = BIT.from_py(0)
    m.IS_RST_INVERTED = BIT.from_py(0)
    m.REF_JITTER1 = 0.01
    m.REF_JITTER2 = 0.01
    m.SS_EN = "FALSE"
    m.SS_MODE = "CENTER_HIGH"
    m.SS_MOD_PERIOD = 10000
    m.STARTUP_WAIT = "FALSE"

    print(to_rtl_str(m, target_platform=XilinxVivadoPlatform()))
