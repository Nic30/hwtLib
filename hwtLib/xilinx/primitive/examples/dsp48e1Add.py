#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import Concat, Or, If
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import HandshakeSync, VectSignal, Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.xilinx.primitive.dsp48e1 import DSP48E1
from hwtLib.xilinx.primitive.dsp48e1_constants import ALU_MODE, CARRYIN_SEL, \
    get_inmode, MUL_A_SEL, MUL_B_SEL, get_opmode, X_SEL, Y_SEL, Z_SEL
from hwtSimApi.hdlSimulator import HdlSimulator
from pyMathBitPrecise.bit_utils import apply_set_and_clear
from hwt.code_utils import rename_signal
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from typing import List
from hwt.synthesizer.vectorUtils import fitTo
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.hdl.value import HValue


class Dsp48e1AluInputAG(HandshakedAgent):

    def get_data(self):
        i = self.intf
        return (i.a.read(), i.b.read())

    def set_data(self, data):
        i = self.intf
        if data is None:
            a = None
            b = None
        else:
            a, b = data
        i.a.write(a)
        i.b.write(b)


class Dsp48e1AluInput(HandshakeSync):

    def _config(self):
        self.DATA_WIDTH = Param(48)
        self.REG_IN = Param(True)
        self.REG_OUT = Param(True)

    def _declr(self):
        self.a = VectSignal(self.DATA_WIDTH)
        self.b = VectSignal(self.DATA_WIDTH)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = Dsp48e1AluInputAG(sim, self)


def generate_handshake_pipe_cntrl(parent: Unit, n: int, name_prefix: str, in_valid: RtlSignal, out_ready: RtlSignal):
    """
    An utility that construct a pipe of registers to store the validity status of a register in the pipeline.
    These registers are connected in pipeline and synchronized by handshake logic.
    Clock enable signal for each stage in pipeline is also provided.

    :ivar ~.n: number of stages
    """
    clock_enables = []
    valids = []
    for i in range(n):
        vld = parent._reg(f"{name_prefix:s}_{i:d}_valid", def_val=0)
        valids.append(vld)
        ce = parent._sig(f"{name_prefix:s}_{i:d}_clock_enable")
        clock_enables.append(ce)

    in_ready = out_ready
    for i, (vld, ce) in enumerate(zip(valids, clock_enables)):
        rd = rename_signal(parent,
                           Or(*[~_vld for _vld in valids[i + 1:]], out_ready),
                           f"{name_prefix:s}_{i:d}_ready")
        if i == 0:
            in_ready = rd | ~vld
            prev_vld = in_valid
        else:
            prev_vld = valids[i - 1]

        vld(apply_set_and_clear(vld, prev_vld, rd))
        ce(~vld | (rd & prev_vld))

    if n:
        out_valid = valids[-1]
    else:
        out_valid = in_valid

    return clock_enables, valids, in_ready, out_valid


class Dsp48e1Add(Unit):

    def _config(self):
        self.DATA_WIDTH = Param(48)
        self.REG_IN = Param(False)
        self.REG_OUT = Param(False)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.data_in = Dsp48e1AluInput()
            self.data_out = Handshaked()._m()

    def set_mode(self, dsp):
        dsp.INMODE(get_inmode(dsp.AREG, dsp.USE_DPORT, MUL_A_SEL.A2, MUL_B_SEL.B2))
        dsp.OPMODE(get_opmode(X_SEL.A_B, Y_SEL.ZERO, Z_SEL.C))
        dsp.ALUMODE(ALU_MODE["Z + X + Y + CIN"])

    def postpone_val(self, sig_in, clock_enables: List[RtlSignal], name_prefix=None):
        """
        Generate a register pipeline which can be used to dealy a value, the length of pipeline
        is derived from number of clock_enable signals
        """
        if isinstance(sig_in, (int, HValue)):
            return sig_in

        if name_prefix is None:
            name_prefix = getSignalName(sig_in)
        out = sig_in
        for st_i, ce in enumerate(clock_enables):
            r = self._reg(f"{name_prefix:s}_{st_i:d}", dtype=out._dtype)
            If(ce,
               r(out)
            )
            out = r
        return out

    def _impl(self):
        REG_IN = self.REG_IN
        REQUIRES_CASCADE = self.REG_OUT and self.DATA_WIDTH > 48

        dsps = HObjList()
        for i in range(ceil(self.DATA_WIDTH / 48)):
            dsp = DSP48E1()
            dsp.A_INPUT = "DIRECT"
            dsp.B_INPUT = "DIRECT"
            dsp.USE_DPORT = "FALSE"

            dsp.ACASCREG = \
            dsp.ALUMODEREG = \
            dsp.AREG = \
            dsp.BCASCREG = \
            dsp.BREG = \
            dsp.CARRYINSELREG = \
            dsp.CREG = int(REG_IN or (REQUIRES_CASCADE and i > 0))

            dsp.ADREG = 0
            dsp.CARRYINSELREG = 0
            dsp.DREG = 0
            dsp.INMODEREG = 0
            dsp.MREG = 0
            dsp.OPMODEREG = 1
            dsp.PREG = int(self.REG_OUT)
            dsp.USE_MULT = "NONE"
            dsp.USE_SIMD = "ONE48"
            dsps.append(dsp)

        self.dsp = dsps

        carry = 0
        carry_column = 0
        dsp_outputs = []
        din = self.data_in
        dout = self.data_out
        dsp_clock_enables = []
        dsp_inputs = []
        for i, dsp in enumerate(dsps):
            offset = i * 48
            width = min(48, self.DATA_WIDTH - offset)
            if width <= 18:
                a = 0
                b = din.b[offset + width:offset]
            else:
                a = din.b[offset + width:18 + offset]
                b = din.b[offset + 18:offset]

            c = din.a[offset + width:offset]
            dsp_inputs.append((a, b, c))

        # register to wait 1 clock before 1st operation to load operation and operand selection registers
        mode_preload = self._reg("mode_preload", def_val=1)
        mode_preload(0)
        if REQUIRES_CASCADE:
            # cascade is required because carry out signal has register and thus the input data
            # to a next DSP has to be delayed
            assert self.REG_OUT
            stage_cnt = int(self.REG_IN) + int(self.REG_OUT) + ceil(self.DATA_WIDTH / 48) - 1
            clock_enables, _, in_ready, out_valid = generate_handshake_pipe_cntrl(
                self, stage_cnt, "pipe_reg", din.vld & ~mode_preload, dout.rd)

            delayed_dsp_inputs = []
            for i, (dsp, (a, b, c)) in enumerate(zip(dsps, dsp_inputs)):
                if self.REG_IN:
                    input_ces = clock_enables[:i]
                    ce_0 = clock_enables[i]
                    ce_1 = clock_enables[i + 1]
                else:
                    if i == 0:
                        # :note: only first does not have in registers
                        ce_0 = 1
                        ce_1 = clock_enables[i]
                        input_ces = []
                    else:
                        ce_0 = clock_enables[i - 1]
                        ce_1 = clock_enables[i]
                        input_ces = clock_enables[:i - 1] # because the last register is a part of DPS

                dsp_clock_enables.append((ce_0, ce_1))

                a_delayed = self.postpone_val(a, input_ces, f"a{i:d}_")
                b_delayed = self.postpone_val(b, input_ces, f"b{i:d}_")
                c_delayed = self.postpone_val(c, input_ces, f"c{i:d}_")
                delayed_dsp_inputs.append((a_delayed, b_delayed, c_delayed))

            dsp_inputs = delayed_dsp_inputs
        else:
            stage_cnt = int(self.REG_IN) + int(self.REG_OUT)
            clock_enables, _, in_ready, out_valid = generate_handshake_pipe_cntrl(
                self, stage_cnt, "pipe_reg", din.vld & ~mode_preload, dout.rd)

            if self.REG_IN:
                ce_0 = clock_enables[0]
            else:
                ce_0 = 1

            if self.REG_OUT:
                if self.REG_IN:
                    ce_1 = clock_enables[1]
                else:
                    ce_1 = clock_enables[0]
            else:
                ce_1 = 1

            for i, dsp in enumerate(dsps):
                dsp_clock_enables.append((mode_preload | ce_0, mode_preload | ce_1))

        dout.vld(out_valid & ~mode_preload)
        din.rd(in_ready & ~mode_preload)

        for i, (dsp, (ce_0, ce_1), (a, b, c)) in enumerate(zip(dsps, dsp_clock_enables, dsp_inputs)):
            offset = i * 48
            width = min(48, self.DATA_WIDTH - offset)

            dsp.CLK(self.clk)
            dsp.ACIN(0)
            dsp.BCIN(0)
            dsp.MULTSIGNIN(1)
            dsp.PCIN(0)
            dsp.CEINMODE(1)
            self.set_mode(dsp)
            dsp.RSTINMODE(0)

            if i == 0:
                dsp.CARRYINSEL(CARRYIN_SEL.CARRYIN.value)
                dsp.CARRYIN(carry)
                dsp.CARRYCASCIN(carry_column)
                carry = dsp.CARRYOUT[3]
                carry_column = dsp.CARRYCASCOUT
            else:
                dsp.CARRYINSEL(CARRYIN_SEL.CARRYCASCIN.value)
                dsp.CARRYIN(0)
                dsp.CARRYCASCIN(carry_column)
                carry_column = dsp.CARRYCASCOUT

            if width <= 18:
                assert isinstance(a, int) and a == 0, a
                dsp.A(a)
                dsp.B(fitTo(b, dsp.B, shrink=False))
                dsp.C(fitTo(c, dsp.C, shrink=False))
            elif width < 48:
                dsp.A(fitTo(a, dsp.A, shrink=False))
                dsp.B(b)
                dsp.C(fitTo(c, dsp.C, shrink=False))
            else:
                dsp.A(a)
                dsp.B(b)
                dsp.C(c)

            dsp.D(0)
            dsp_outputs.append(dsp.P[width:])

            for _ce in [
                    dsp.CEA1,
                    dsp.CEA2,
                    dsp.CEALUMODE,
                    dsp.CEB2,
                    dsp.CEB1,
                    dsp.CEC,
                    dsp.CECARRYIN,
                    dsp.CECTRL,
                ]:
                _ce(ce_0)
            for _ce in [dsp.CEAD, dsp.CED, dsp.CEM]:
                _ce(1)

            dsp.CEP(ce_1)

            for _rst in [dsp.RSTA,
                dsp.RSTALLCARRYIN,
                dsp.RSTALUMODE,
                dsp.RSTB,
                dsp.RSTC,
                dsp.RSTCTRL,
                dsp.RSTD,
                dsp.RSTM,
                dsp.RSTP,]:
                _rst(~self.rst_n)

        if REQUIRES_CASCADE:
            delayed_dsp_outputs = []
            max_delay = len(dsp_outputs) - 1
            for i, out in enumerate(dsp_outputs):
                delay = max_delay - i
                if delay > 0:
                    # select n last
                    ces = clock_enables[-delay:]
                    delayed_out = self.postpone_val(out, ces, f"out_delay_{i:d}")
                else:
                    delayed_out = out
                delayed_dsp_outputs.append(delayed_out)
            dsp_outputs = delayed_dsp_outputs
        dout.data(Concat(*reversed(dsp_outputs)))


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Dsp48e1Add()
    u.REG_IN = True
    u.REG_OUT = False
    u.DATA_WIDTH = 48
    print(to_rtl_str(u))

