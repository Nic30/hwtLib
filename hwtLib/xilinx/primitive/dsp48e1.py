#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch, Concat, In, And, replicate
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import  BIT
from hwt.interfaces.std import Signal, Clk
from hwt.serializer.mode import serializeExclude
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.xilinx.primitive.dsp48e1_constants import LOGIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1, \
    LOGIC_MODES_DRC_deassign_xyz_mux, ARITHMETIC_MODES_DRC_deassign_xyz_mux, \
    ARITHMETIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1, CARRYIN_SEL
from pyMathBitPrecise.bit_utils import mask


@serializeExclude
class DSP48E1(Unit):
    """
    DSP hadblock in Xilinx 7 series (2x pre adder, multiplier, ALU)

    :see: https://www.xilinx.com/support/documentation/user_guides/ug479_7Series_DSP48E1.pdf
    """

    def _config(self):
        self.ACASCREG = Param(1)
        self.ADREG = Param(1)
        self.ALUMODEREG = Param(1)
        self.AREG = Param(1)
        self.AUTORESET_PATDET = Param("NO_RESET")
        self.A_INPUT = Param("DIRECT")
        self.BCASCREG = Param(1)
        self.BREG = Param(1)
        self.B_INPUT = Param("DIRECT")
        self.CARRYINREG = Param(1)
        self.CARRYINSELREG = Param(1)
        self.CREG = Param(1)
        self.DREG = Param(1)
        self.INMODEREG = Param(1)
        self.IS_ALUMODE_INVERTED = Param(Bits(4).from_py(0b0000))
        self.IS_CARRYIN_INVERTED = Param(BIT.from_py(0b0))
        self.IS_CLK_INVERTED = Param(BIT.from_py(0b0))
        self.IS_INMODE_INVERTED = Param(Bits(5).from_py(0b00000))
        self.IS_OPMODE_INVERTED = Param(Bits(7).from_py(0b0000000))
        self.MASK = Param(Bits(48).from_py(0x3fffffffffff))
        self.MREG = Param(1)
        self.OPMODEREG = Param(1)
        self.PATTERN = Param(Bits(48).from_py(0x000000000000))
        self.PREG = Param(1)
        self.SEL_MASK = Param("MASK")
        self.SEL_PATTERN = Param("PATTERN")
        self.USE_DPORT = Param("FALSE")
        self.USE_MULT = Param("MULTIPLY")
        self.USE_PATTERN_DETECT = Param("NO_PATDET")
        self.USE_SIMD = Param("ONE48")

    def deassign_xyz_mux(self):
        return [
            self.opmode_valid_flag(1),
            self.invalid_opmode(1)
        ]

    def display_invalid_opmode(self):
        return [
            self.opmode_valid_flag(0),
            self.invalid_opmode(0),
            # print("OPMODE Input Warning : The OPMODE %b requires attribute PREG set to 1.", qopmode_o_mux, sim.now // 1000.000000)
        ]

    def _declr(self):
        self.CLK = Clk()

        # inputs
        self.A = Signal(Bits(30))
        self.B = Signal(Bits(18))
        self.C = Signal(Bits(48))
        self.D = Signal(Bits(25))
        # selects the operands for main ALU
        # [2:0] X
        # [4:2] Y
        # [7:4] Z
        self.OPMODE = Signal(Bits(7))
        # :ivar ALUMODE: selects the operation performed by main ALU
        self.ALUMODE = Signal(Bits(4))
        self.CECARRYIN = Signal()
        self.CARRYINSEL = Signal(Bits(3))
        # :ivar INMODE: Select the functionality of the pre-adder, the A,
        # B, and D inputs, and the input registers. These bits should default to
        # 5’b00000 if left unconnected. These are optionally invertible,
        # providing routing flexibility.
        self.INMODE = Signal(Bits(5))
        self.CARRYIN = Signal()

        # main outputs
        self.OVERFLOW = Signal()._m()
        self.P = Signal(Bits(48))._m()
        self.PATTERNBDETECT = Signal()._m()
        self.PATTERNDETECT = Signal()._m()
        self.UNDERFLOW = Signal()._m()
        self.CARRYOUT = Signal(Bits(4))._m()

        # clock enable for internal registers
        self.CEA1 = Signal()
        self.CEA2 = Signal()
        self.CEAD = Signal()
        self.CEB1 = Signal()
        self.CEB2 = Signal()
        self.CEC = Signal()
        self.CED = Signal()
        self.CEM = Signal()
        self.CEP = Signal()
        self.CEALUMODE = Signal()
        self.CECTRL = Signal()
        self.CEINMODE = Signal()

        # reset for internal registers
        self.RSTA = Signal()
        self.RSTALLCARRYIN = Signal()
        self.RSTALUMODE = Signal()
        self.RSTB = Signal()
        self.RSTC = Signal()
        self.RSTCTRL = Signal()
        self.RSTD = Signal()
        self.RSTINMODE = Signal()
        self.RSTM = Signal()
        self.RSTP = Signal()

        # Column ports are used to connect the DSP blocks in the column
        #  and they have an equivalent port for fabric (e.g. A and ACIN).
        self.ACIN = Signal(Bits(30))
        self.ACOUT = Signal(Bits(30))._m()
        self.BCIN = Signal(Bits(18))
        self.BCOUT = Signal(Bits(18))._m()
        # cary in/out for main ALU
        self.CARRYCASCIN = Signal()
        self.CARRYCASCOUT = Signal()._m()
        self.PCIN = Signal(Bits(48))
        self.PCOUT = Signal(Bits(48))._m()
        # Sign of the multiplied result from the previous DSP48E1 slice for MACC extension.
        self.MULTSIGNIN = Signal()
        self.MULTSIGNOUT = Signal()._m()

        self.input_check()

    def input_check(self):
        assert self.A_INPUT in ("DIRECT", "CASCADE"), self.A_INPUT
        assert self.ALUMODEREG in (0, 1), self.ALUMODEREG

        #-------- (ACASCREG) and (ACASCREG vs AREG) check
        if self.AREG in (0, 1):
            if self.AREG != self.ACASCREG:
                raise AssertionError(f"ACASCREG  is set to {self.ACASCREG}. ACASCREG has to be set to same value as AREG.")
        elif self.AREG == 2:
            if self.AREG != self.ACASCREG and self.AREG - 1 != self.ACASCREG:
                raise AssertionError(f"ACASCREG is set to {self.ACASCREG}. ACASCREG has to be set to either 2 or 1 when AREG = 2.")
        else:
            raise AssertionError(f"AREG is set to {self.AREG}.")

        assert self.B_INPUT in ("DIRECT", "CASCADE"), self.B_INPUT

        #-------- (BCASCREG) and (BCASCREG vs BREG) check
        if self.BREG in (0, 1):
            if self.BREG != self.BCASCREG:
                raise AssertionError(f"BCASCREG is set to {self.BCASCREG}. BCASCREG has to be set to same value as BREG.")
        elif self.BREG == 2:
            if self.BREG != self.BCASCREG and self.BREG - 1 != self.BCASCREG:
                raise AssertionError(f"BCASCREG is set to {self.BCASCREG}. BCASCREG has to be set to either 2 or 1 when BREG = 2.")
        else:
            raise AssertionError(f"BREG is set to {self.BREG}.")


        assert self.CARRYINREG in (0, 1), self.CARRYINREG
        assert self.CARRYINSELREG in (0, 1), self.CARRYINSELREG
        assert self.CREG in (0, 1), self.CREG
        assert self.OPMODEREG in (0, 1), self.OPMODEREG
        assert self.USE_MULT in ("NONE", "MULTIPLY", "DYNAMIC"), self.USE_MULT
        assert self.USE_PATTERN_DETECT in ("PATDET", "NO_PATDET"), self.USE_PATTERN_DETECT
        assert self.AUTORESET_PATDET in ("NO_RESET", "RESET_MATCH", "RESET_NOT_MATCH"), self.AUTORESET_PATDET
        assert self.SEL_PATTERN in ("PATTERN", "C"), self.SEL_PATTERN
        assert self.SEL_MASK in ("MASK", "C", "ROUNDING_MODE1", "ROUNDING_MODE2"), self.SEL_MASK
        assert self.MREG in (0, 1), self.MREG
        assert self.PREG in (0, 1), self.PREG
        assert self.ADREG in (0, 1), self.ADREG
        assert self.DREG in (0, 1), self.DREG
        assert self.INMODEREG in (0, 1), self.INMODEREG
        assert self.USE_DPORT in ("TRUE", "FALSE"), self.USE_DPORT

        if self.USE_MULT == "NONE" and self.MREG != 0:
            raise AssertionError(f"Attribute USE_MULT is set to \"NONE\" and MREG is set to {self.MREG}. MREG must be set to 0 when the multiplier is not used.")

    def _impl(self):
        # internal signals
        ACASCREG, ADREG, ALUMODEREG, AREG, AUTORESET_PATDET, A_INPUT, BCASCREG, BREG, B_INPUT, CARRYINREG, CARRYINSELREG, \
        CREG, DREG, INMODEREG, IS_ALUMODE_INVERTED, IS_CARRYIN_INVERTED, IS_CLK_INVERTED, IS_INMODE_INVERTED, IS_OPMODE_INVERTED, MASK, MREG, \
        OPMODEREG, PATTERN, PREG, SEL_MASK, SEL_PATTERN, USE_DPORT, USE_MULT, USE_PATTERN_DETECT, USE_SIMD, ACOUT, \
        BCOUT, CARRYCASCOUT, CARRYOUT, MULTSIGNOUT, OVERFLOW, P, PATTERNBDETECT, PATTERNDETECT, PCOUT, UNDERFLOW, \
        A, ACIN, ALUMODE, B, BCIN, C, CARRYCASCIN, CARRYIN, CARRYINSEL, CEA1, \
        CEA2, CEAD, CEALUMODE, CEB1, CEB2, CEC, CECARRYIN, CECTRL, CED, CEINMODE, \
        CEM, CEP, CLK, D, INMODE, MULTSIGNIN, OPMODE, PCIN, RSTA, RSTALLCARRYIN, \
        RSTALUMODE, RSTB, RSTC, RSTCTRL, RSTD, RSTINMODE, RSTM, RSTP = \
        self.ACASCREG, self.ADREG, self.ALUMODEREG, self.AREG, self.AUTORESET_PATDET, self.A_INPUT, self.BCASCREG, self.BREG, self.B_INPUT, self.CARRYINREG, self.CARRYINSELREG, \
        self.CREG, self.DREG, self.INMODEREG, self.IS_ALUMODE_INVERTED, self.IS_CARRYIN_INVERTED, self.IS_CLK_INVERTED, self.IS_INMODE_INVERTED, self.IS_OPMODE_INVERTED, self.MASK, self.MREG, \
        self.OPMODEREG, self.PATTERN, self.PREG, self.SEL_MASK, self.SEL_PATTERN, self.USE_DPORT, self.USE_MULT, self.USE_PATTERN_DETECT, self.USE_SIMD, self.ACOUT, \
        self.BCOUT, self.CARRYCASCOUT, self.CARRYOUT, self.MULTSIGNOUT, self.OVERFLOW, self.P, self.PATTERNBDETECT, self.PATTERNDETECT, self.PCOUT, self.UNDERFLOW, \
        self.A, self.ACIN, self.ALUMODE, self.B, self.BCIN, self.C, self.CARRYCASCIN, self.CARRYIN, self.CARRYINSEL, self.CEA1, \
        self.CEA2, self.CEAD, self.CEALUMODE, self.CEB1, self.CEB2, self.CEC, self.CECARRYIN, self.CECTRL, self.CED, self.CEINMODE, \
        self.CEM, self.CEP, self.CLK, self.D, self.INMODE, self.MULTSIGNIN, self.OPMODE, self.PCIN, self.RSTA, self.RSTALLCARRYIN, \
        self.RSTALUMODE, self.RSTB, self.RSTC, self.RSTCTRL, self.RSTD, self.RSTINMODE, self.RSTM, self.RSTP
        #------------------- constants -------------------------
        CARRYOUT_W = 4
        A_W = 30
        ALUMODE_W = 4
        A_MULT_W = 25
        B_W = 18
        B_MULT_W = 18
        D_W = 25
        INMODE_W = 5
        OPMODE_W = 7
        ALU_FULL_W = 48

        IS_ALUMODE_INVERTED_BIN = self._sig("IS_ALUMODE_INVERTED_BIN", Bits(4), def_val=IS_ALUMODE_INVERTED)
        IS_CARRYIN_INVERTED_BIN = self._sig("IS_CARRYIN_INVERTED_BIN", def_val=IS_CARRYIN_INVERTED)
        IS_CLK_INVERTED_BIN = self._sig("IS_CLK_INVERTED_BIN", def_val=IS_CLK_INVERTED)
        IS_INMODE_INVERTED_BIN = self._sig("IS_INMODE_INVERTED_BIN", Bits(5), def_val=IS_INMODE_INVERTED)
        IS_OPMODE_INVERTED_BIN = self._sig("IS_OPMODE_INVERTED_BIN", Bits(7), def_val=IS_OPMODE_INVERTED)
        a_o_mux = self._sig("a_o_mux", Bits(30))
        qa_o_mux = self._sig("qa_o_mux", Bits(30))
        qa_o_reg1 = self._sig("qa_o_reg1", Bits(30))
        qa_o_reg2 = self._sig("qa_o_reg2", Bits(30))
        qacout_o_mux = self._sig("qacout_o_mux", Bits(30))
        # new
        qinmode_o_mux = self._sig("qinmode_o_mux", Bits(5))
        qinmode_o_reg = self._sig("qinmode_o_reg", Bits(5))
        # new
        a_preaddsub = self._sig("a_preaddsub", Bits(25))
        b_o_mux = self._sig("b_o_mux", Bits(18))
        qb_o_mux = self._sig("qb_o_mux", Bits(18))
        qb_o_reg1 = self._sig("qb_o_reg1", Bits(18))
        qb_o_reg2 = self._sig("qb_o_reg2", Bits(18))
        qbcout_o_mux = self._sig("qbcout_o_mux", Bits(18))
        qcarryinsel_o_mux = self._sig("qcarryinsel_o_mux", Bits(3))
        qcarryinsel_o_reg1 = self._sig("qcarryinsel_o_reg1", Bits(3))
        # new
        #d_o_mux = self._sig("d_o_mux", Bits(D_W))
        qd_o_mux = self._sig("qd_o_mux", Bits(D_W))
        qd_o_reg1 = self._sig("qd_o_reg1", Bits(D_W))
        qmult_o_mux = self._sig("qmult_o_mux", Bits(A_MULT_W + B_MULT_W))
        qmult_o_reg = self._sig("qmult_o_reg", Bits(A_MULT_W + B_MULT_W))
        # 42:0
        qc_o_mux = self._sig("qc_o_mux", Bits(48))
        qc_o_reg1 = self._sig("qc_o_reg1", Bits(48))
        qp_o_mux = self._sig("qp_o_mux", Bits(48))
        qp_o_reg1 = self._sig("qp_o_reg1", Bits(48))
        qx_o_mux = self._sig("qx_o_mux", Bits(48))
        qy_o_mux = self._sig("qy_o_mux", Bits(48))
        qz_o_mux = self._sig("qz_o_mux", Bits(48))
        qopmode_o_mux = self._sig("qopmode_o_mux", Bits(7))
        qopmode_o_reg1 = self._sig("qopmode_o_reg1", Bits(7))
        qcarryin_o_mux0 = self._sig("qcarryin_o_mux0")
        qcarryin_o_reg0 = self._sig("qcarryin_o_reg0")
        qcarryin_o_mux7 = self._sig("qcarryin_o_mux7")
        qcarryin_o_reg7 = self._sig("qcarryin_o_reg7")
        qcarryin_o_mux = self._sig("qcarryin_o_mux")
        qalumode_o_mux = self._sig("qalumode_o_mux", Bits(4))
        qalumode_o_reg1 = self._sig("qalumode_o_reg1", Bits(4))
        self.invalid_opmode = self._sig("invalid_opmode", def_val=1)
        self.opmode_valid_flag = opmode_valid_flag = self._sig("opmode_valid_flag", def_val=1)
        #   reg [47:0] alu_o;
        alu_o = self._sig("alu_o", Bits(48))
        qmultsignout_o_reg = self._sig("qmultsignout_o_reg")
        multsignout_o_mux = self._sig("multsignout_o_mux")
        multsignout_o_opmode = self._sig("multsignout_o_opmode")
        pdet_o_mux = self._sig("pdet_o_mux")
        pdetb_o_mux = self._sig("pdetb_o_mux")
        the_pattern = self._sig("the_pattern", Bits(48))
        the_mask = self._sig("the_mask", Bits(48), def_val=0)
        carrycascout_o = self._sig("carrycascout_o")
        the_auto_reset_patdet = self._sig("the_auto_reset_patdet")
        carrycascout_o_reg = self._sig("carrycascout_o_reg", def_val=0)
        carrycascout_o_mux = self._sig("carrycascout_o_mux", def_val=0)

        # CR 588861
        carryout_o_reg = self._sig("carryout_o_reg", Bits(4), def_val=0)
        carryout_o_mux = self._sig("carryout_o_mux", Bits(4))
        carryout_x_o = self._sig("carryout_x_o", Bits(4))
        pdet_o = self._sig("pdet_o")
        pdetb_o = self._sig("pdetb_o")
        pdet_o_reg1 = self._sig("pdet_o_reg1")
        pdet_o_reg2 = self._sig("pdet_o_reg2")
        pdetb_o_reg1 = self._sig("pdetb_o_reg1")
        pdetb_o_reg2 = self._sig("pdetb_o_reg2")
        overflow_o = self._sig("overflow_o")
        underflow_o = self._sig("underflow_o")
        mult_o = self._sig("mult_o", Bits(A_MULT_W + B_MULT_W))
        #   reg [(MSB_A_MULT+MSB_B_MULT+1):0] mult_o;  // 42:0
        # new
        ad_addsub = self._sig("ad_addsub", Bits(A_MULT_W))
        ad_mult = self._sig("ad_mult", Bits(A_MULT_W))
        qad_o_reg1 = self._sig("qad_o_reg1", Bits(A_MULT_W))
        qad_o_mux = self._sig("qad_o_mux", Bits(A_MULT_W))
        b_mult = self._sig("b_mult", Bits(B_MULT_W))
        # cci_drc_msg = self._sig("cci_drc_msg", def_val=0b0)
        # cis_drc_msg = self._sig("cis_drc_msg", def_val=0b0)
        opmode_in = self._sig("opmode_in", Bits(OPMODE_W))
        alumode_in = self._sig("alumode_in", Bits(ALUMODE_W))
        carryin_in = self._sig("carryin_in")
        clk_in = self._sig("clk_in")
        inmode_in = self._sig("inmode_in", Bits(INMODE_W))
        #*** Y mux
        # 08-06-08
        # IR 478378
        y_mac_cascd = rename_signal(self, qopmode_o_mux[7:4]._eq(0b100)._ternary(replicate(48, MULTSIGNIN), Bits(48).from_py(mask(48))), "y_mac_cascd")
        #--####################################################################
        #--#####                         ALU                              #####
        #--####################################################################
        co = self._sig("co", Bits(ALU_FULL_W))
        s = self._sig("s", Bits(ALU_FULL_W))
        comux = self._sig("comux", Bits(ALU_FULL_W))
        smux = self._sig("smux", Bits(ALU_FULL_W))
        carryout_o = self._sig("carryout_o", Bits(CARRYOUT_W))
        # FINAL ADDER
        s0 = rename_signal(self, Concat(BIT.from_py(0), comux[11:0], qcarryin_o_mux) + Concat(BIT.from_py(0), smux[12:0]), "s0")
        cout0 = rename_signal(self, comux[11] + s0[12], "cout0")
        C1 = rename_signal(self, BIT.from_py(0b0) if USE_SIMD == "FOUR12" else s0[12], "C1")
        co11_lsb = rename_signal(self, BIT.from_py(0b0) if USE_SIMD == "FOUR12" else comux[11], "co11_lsb")
        s1 = rename_signal(self, Concat(BIT.from_py(0), comux[23:12], co11_lsb) + Concat(BIT.from_py(0), smux[24:12]) + Concat(Bits(12).from_py(0), C1), "s1")
        cout1 = rename_signal(self, comux[23] + s1[12], "cout1")
        C2 = rename_signal(self, BIT.from_py(0b0) if (USE_SIMD in ["TWO24", "FOUR12"]) else s1[12], "C2")
        co23_lsb = rename_signal(self, BIT.from_py(0b0) if (USE_SIMD in ["TWO24", "FOUR12"]) else comux[23], "co23_lsb")
        s2 = rename_signal(self, Concat(BIT.from_py(0), comux[35:24], co23_lsb) + Concat(BIT.from_py(0), smux[36:24]) + Concat(Bits(12).from_py(0), C2), "s2")
        cout2 = rename_signal(self, comux[35] + s2[12], "cout2")
        C3 = rename_signal(self, BIT.from_py(0b0) if  USE_SIMD == "FOUR12" else s2[12], "C3")
        co35_lsb = rename_signal(self, BIT.from_py(0b0) if  USE_SIMD == "FOUR12" else comux[35], "co35_lsb")
        s3 = rename_signal(self, Concat(BIT.from_py(0), comux[48:36], co35_lsb) + Concat(Bits(2).from_py(0), smux[48:36]) + Concat(Bits(13).from_py(0), C3), "s3")
        cout3 = rename_signal(self, s3[12], "cout3")
        #cout4 = rename_signal(self, s3[13], "cout4")
        qcarryin_o_mux_tmp = self._sig("qcarryin_o_mux_tmp")

        ACOUT(qacout_o_mux)
        BCOUT(qbcout_o_mux)
        CARRYCASCOUT(carrycascout_o_mux)
        CARRYOUT(carryout_x_o)
        MULTSIGNOUT(multsignout_o_mux)
        OVERFLOW(overflow_o)
        P(qp_o_mux)
        PCOUT(qp_o_mux)
        PATTERNDETECT(pdet_o_mux)
        PATTERNBDETECT(pdetb_o_mux)
        UNDERFLOW(underflow_o)
        alumode_in(ALUMODE ^ IS_ALUMODE_INVERTED_BIN)
        carryin_in(CARRYIN ^ IS_CARRYIN_INVERTED_BIN)
        clk_in(CLK ^ IS_CLK_INVERTED_BIN)
        inmode_in(INMODE ^ IS_INMODE_INVERTED_BIN)
        opmode_in(OPMODE ^ IS_OPMODE_INVERTED_BIN)

        #*********************************************************
        #**********  INMODE signal registering        ************
        #*********************************************************
        If(clk_in._onRisingEdge(),
            If(RSTINMODE,
                qinmode_o_reg(0b0)
            ).Elif(CEINMODE,
                qinmode_o_reg(inmode_in)
            )
        )
        if INMODEREG == 0:
            qinmode_o_mux(inmode_in)
        elif INMODEREG == 1:
            qinmode_o_mux(qinmode_o_reg)
        else:
            raise AssertionError()

        if A_INPUT == "DIRECT":
            a_o_mux(A)
        elif A_INPUT == "CASCADE":
            a_o_mux(ACIN)
        else:
            raise AssertionError()

        if AREG in (1, 2):
            If(clk_in._onRisingEdge(),
                If(RSTA,
                    qa_o_reg1(0b0),
                    qa_o_reg2(0b0)
                ).Else(
                    If(CEA1,
                        qa_o_reg1(a_o_mux)
                    ),
                    If(CEA2,
                        qa_o_reg2(a_o_mux if AREG == 1 else
                                  qa_o_reg1 if AREG == 2 else
                                  None)
                    )
                )
            )
        else:
            qa_o_reg1(None)


        if AREG == 0:
            qa_o_mux(a_o_mux)
        elif AREG == 1:
            qa_o_mux(qa_o_reg2)
        elif AREG == 2:
            qa_o_mux(qa_o_reg2)
        else:
            raise AssertionError()

        if ACASCREG == 1:
            qacout_o_mux(qa_o_reg1 if AREG == 2 else qa_o_mux)
        elif ACASCREG == 0:
            qacout_o_mux(qa_o_mux)
        elif ACASCREG == 2:
            qacout_o_mux(qa_o_mux)
        else:
            raise AssertionError()

        If(qinmode_o_mux[1],
           a_preaddsub(0b0)
        ).Elif(qinmode_o_mux[0],
            a_preaddsub(qa_o_reg1[25:0]),
        ).Else(
            a_preaddsub(qa_o_mux[25:0]),
        )
        if B_INPUT == "DIRECT":
            b_o_mux(B)
        elif B_INPUT == "CASCADE":
            b_o_mux(BCIN)
        else:
            raise AssertionError()

        if BREG in (1, 2):
            If(clk_in._onRisingEdge(),
                If(RSTB,
                    qb_o_reg1(0b0),
                    qb_o_reg2(0b0)
                ).Else(
                    If(CEB1,
                        qb_o_reg1(b_o_mux)
                    ),
                    If(CEB2,
                        qb_o_reg2(b_o_mux if BREG == 1 else
                                  qb_o_reg1 if BREG == 1 else
                                  None)
                    )
                )
            )
        else:
            qb_o_reg1(None)

        if BREG == 0:
            qb_o_mux(b_o_mux)
        elif BREG == 1:
            qb_o_mux(qb_o_reg2)
        elif BREG == 2:
            qb_o_mux(qb_o_reg2)
        else:
            raise AssertionError()

        if BCASCREG == 1:
            qbcout_o_mux(qb_o_reg1 if BREG == 2 else qb_o_mux)
        elif BCASCREG == 0:
            qbcout_o_mux(qb_o_mux)
        elif BCASCREG == 2:
            qbcout_o_mux(qb_o_mux)
        else:
            raise AssertionError()

        b_mult(qinmode_o_mux[4]._ternary(qb_o_reg1, qb_o_mux))

        #*********************************************************
        #*** Input register C with 1 level deep of register
        #*********************************************************
        If(clk_in._onRisingEdge(),
            If(RSTC,
                qc_o_reg1(0b0)
            ).Elif(CEC,
                qc_o_reg1(C)
            )
        )
        if CREG == 0:
            qc_o_mux(C)
        elif CREG == 1:
            qc_o_mux(qc_o_reg1)
        else:
            raise AssertionError()

        #*********************************************************
        #*** Input register D with 1 level deep of register
        #*********************************************************
        If(clk_in._onRisingEdge(),
            If(RSTD,
                qd_o_reg1(0b0)
            ).Elif(CED,
                qd_o_reg1(D)
            )
        )
        if DREG == 0:
            qd_o_mux(D)
        elif DREG == 1:
            qd_o_mux(qd_o_reg1)
        else:
            raise AssertionError()

        ad_addsub(qinmode_o_mux[3]._ternary(-a_preaddsub + qinmode_o_mux[2]._ternary(qd_o_mux, 0b0),
                                             a_preaddsub + qinmode_o_mux[2]._ternary(qd_o_mux, 0b0)))

        If(clk_in._onRisingEdge(),
            If(RSTD,
                qad_o_reg1(0b0)
            ).Elif(CEAD,
                qad_o_reg1(ad_addsub)
            )
        )
        if ADREG == 0:
            qad_o_mux(ad_addsub)
        elif ADREG == 1:
            qad_o_mux(qad_o_reg1)
        else:
            raise AssertionError()

        ad_mult(qad_o_mux if USE_DPORT == "TRUE" else a_preaddsub)

        #*********************************************************
        #*********************************************************
        #***************      25x18 Multiplier     ***************
        #*********************************************************
        # 05/26/05 -- FP -- Added warning for invalid mult when USE_MULT=NONE
        # SIMD=FOUR12 and SIMD=TWO24
        # Made mult_o to be "X"
        if USE_MULT == "NONE" or USE_SIMD != "ONE48":
            mult_o(0b0)
        else:
            If(CARRYINSEL._eq(0b010),
                mult_o(None)
            ).Else(
                mult_o(replicate(18, ad_mult[24])._concat(ad_mult[25:0]) *
                       replicate(25, b_mult[17])._concat(b_mult))
            )

        If(clk_in._onRisingEdge(),
            If(RSTM,
                qmult_o_reg(0b0)
            ).Elif(CEM,
                qmult_o_reg(mult_o)
            )
        )

        If(qcarryinsel_o_mux._eq(0b010),
            qmult_o_mux(None)
        ).Else(
            qmult_o_mux(qmult_o_reg if MREG == 1 else mult_o)
        )

        #*** X mux
        # ask jmt
        # add post 2014.4
        # else
        Switch(qopmode_o_mux[2:0])\
            .Case(0b00,
                # X_SEL.ZERO
                qx_o_mux(0b0))\
            .Case(0b01,
                # X_SEL.M
                qx_o_mux(replicate(5, qmult_o_mux[A_MULT_W + B_MULT_W - 1])._concat(qmult_o_mux)))\
            .Case(0b10,
                # X_SEL.P
                qx_o_mux(qp_o_mux if PREG == 1 else None))\
            .Case(0b11,
                # X_SEL.A_B
                qx_o_mux(None)
                if USE_MULT == "MULTIPLY" and (
                    (AREG == 0 and BREG == 0 and MREG == 0) or
                    (AREG == 0 and BREG == 0 and PREG == 0) or
                    (MREG == 0 and PREG == 0))
                # print("OPMODE Input Warning : The OPMODE[1:0] %b to DSP48E1 instance %m is invalid when using attributes USE_MULT = MULTIPLY at %.3f ns. Please set USE_MULT to either NONE or DYNAMIC.", qopmode_o_mux[slice(2, 0)], sim.now // 1000.000000)
                else qx_o_mux(qa_o_mux[A_W:0]._concat(qb_o_mux[B_W:0]))
            )

        # add post 2014.4
        Switch(qopmode_o_mux[4:2])\
            .Case(0b00,
                qy_o_mux(0b0))\
            .Case(0b01,
                qy_o_mux(0b0))\
            .Case(0b10,
                qy_o_mux(y_mac_cascd))\
            .Case(0b11,
                qy_o_mux(qc_o_mux))

        #*** Z mux
        # ask jmt
        # add post 2014.4
        Switch(qopmode_o_mux[7:4])\
            .Case(0b000,
                qz_o_mux(0b0))\
            .Case(0b001,
                qz_o_mux(PCIN))\
            .Case(0b010,
                qz_o_mux(qp_o_mux))\
            .Case(0b011,
                qz_o_mux(qc_o_mux))\
            .Case(0b100,
                qz_o_mux(qp_o_mux))\
            .Case(0b101,
                qz_o_mux(replicate(17, PCIN[47])._concat(PCIN[48:17])))\
            .Case(0b110,
                qz_o_mux(replicate(17, qp_o_mux[47])._concat(qp_o_mux[48:17])))\
            .Case(0b111,
                qz_o_mux(replicate(17, qp_o_mux[47])._concat(qp_o_mux[48:17])))

        #*** CarryInSel and OpMode with 1 level of register
        If(clk_in._onRisingEdge(),
            If(RSTCTRL,
                qcarryinsel_o_reg1(0b0),
                qopmode_o_reg1(0b0)
            ).Elif(CECTRL,
                qcarryinsel_o_reg1(CARRYINSEL),
                qopmode_o_reg1(opmode_in)
            )
        )
        if CARRYINSELREG == 0:
            qcarryinsel_o_mux(CARRYINSEL)

        elif CARRYINSELREG == 1:
            qcarryinsel_o_mux(qcarryinsel_o_reg1)
        else:
            raise AssertionError()

        # CR 219047 (3)
        # If(qcarryinsel_o_mux._eq(0b010),
        #    If(~((cci_drc_msg._eq(0b1) | qopmode_o_mux._eq(0b1001000)) | (MULTSIGNIN._eq(0b0) & CARRYCASCIN._eq(0b0))),
        #        #print("DRC warning : CARRYCASCIN can only be used in the current DSP48E1 instance %m if the previous DSP48E1 is performing a two input ADD or SUBTRACT operation, or the current DSP48E1 is configured in the MAC extend opmode 7'b1001000 at %.3f ns.", sim.now // 1000.000000),
        #        cci_drc_msg(0b1)
        #    ),
        #    If(~((qopmode_o_mux[4:0] != 0b0101)._isOn())._isOn(),
        #        #print("DRC warning : CARRYINSEL is set to 010 with OPMODE set to multiplication (xxx0101). This is an illegal mode and may show deviation between simulation results and hardware behavior. DSP48E1 instance %m at %.3f ns.", sim.now // 1000.000000)
        #    ),
        #    If(~cis_drc_msg._eq(0b1),
        #        #print("DRC warning : CARRYINSEL is set to 010 with OPMODEREG set to 0. This causes unknown values after reset occurs. It is suggested to use OPMODEREG = 1 when cascading large adders. DSP48E1 instance %m at %.3f ns.", sim.now // 1000.000000),
        #        cis_drc_msg(0b1)
        #    ) if OPMODEREG == 0b1 else []
        # )
        if OPMODEREG == 0:
            qopmode_o_mux(opmode_in)
        elif OPMODEREG == 1:
            qopmode_o_mux(qopmode_o_reg1)
        else:
            raise AssertionError()

        #*** ALUMODE with 1 level of register
        If(clk_in._onRisingEdge(),
            If(RSTALUMODE,
                qalumode_o_reg1(0b0)
            ).Elif(CEALUMODE,
                qalumode_o_reg1(alumode_in)
            )
        )
        if ALUMODEREG == 0:
            qalumode_o_mux(alumode_in)
        elif ALUMODEREG == 1:
            qalumode_o_mux(qalumode_o_reg1)
        else:
            raise AssertionError()

        def deassign_xyz_mux_if_PREG_eq_1():
            if PREG != 1:
                return self.display_invalid_opmode()
            else:
                return self.deassign_xyz_mux()

        def DCR_check_logic_modes():
            # -- LOGIC MODES DRC
            return If(In(qopmode_o_mux, LOGIC_MODES_DRC_deassign_xyz_mux),
                self.deassign_xyz_mux()
            ).Elif(In(qopmode_o_mux, LOGIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1),
                deassign_xyz_mux_if_PREG_eq_1(),
            ).Else(
                # print("OPMODE Input Warning : The OPMODE %b to DSP48E1 instance %m is invalid for LOGIC MODES at %.3f ns.", qopmode_o_mux, sim.now // 1000.000000)
            )

        # display_invalid_opmode
        arith_mode_tmp = qopmode_o_mux._concat(qcarryinsel_o_mux)
        # no check at first 100ns
        Switch(qalumode_o_mux[4:2])\
            .Case(0b00,
                # -- ARITHMETIC MODES DRC
                If(In(arith_mode_tmp, ARITHMETIC_MODES_DRC_deassign_xyz_mux),
                    self.deassign_xyz_mux()
                ).Elif(In(arith_mode_tmp, ARITHMETIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1),
                    deassign_xyz_mux_if_PREG_eq_1()
                ).Else(
                    # CR 444150
                    # If(qopmode_o_mux._concat(qcarryinsel_o_mux)._eq(0b0000000010)._isOn() & (OPMODEREG._eq(1)._isOn() & CARRYINSELREG._eq(0)._isOn())._isOn(),
                    #    print("DRC warning : CARRYINSELREG is set to %d. It is required to have CARRYINSELREG be set to 1 to match OPMODEREG, in order to ensure that the simulation model will match the hardware behavior in all use cases.", CARRYINSELREG)
                    # ),
                    # print("OPMODE Input Warning : The OPMODE %b to DSP48E1 instance %m is either invalid or the CARRYINSEL %b for that specific OPMODE is invalid at %.3f ns. This warning may be due to a mismatch in the OPMODEREG and CARRYINSELREG attribute settings. It is recommended that OPMODEREG and CARRYINSELREG always be set to the same value. ", qopmode_o_mux, qcarryinsel_o_mux, sim.now // 1000.000000)
                )
            )\
            .Case(0b01,
               DCR_check_logic_modes()
            )\
            .Case(0b11,
               DCR_check_logic_modes()
            )\
            .Default(
                # print("OPMODE Input Warning : The OPMODE %b to DSP48E1 instance %m is invalid for LOGIC MODES at %.3f ns.", qopmode_o_mux, sim.now // 1000.000000)
            )

        If(qalumode_o_mux[0],
            co(qx_o_mux & qy_o_mux | ~qz_o_mux & qy_o_mux | qx_o_mux & ~qz_o_mux),
            s(~qz_o_mux ^ qx_o_mux ^ qy_o_mux)
        ).Else(
            co(qx_o_mux & qy_o_mux | qz_o_mux & qy_o_mux | qx_o_mux & qz_o_mux),
            s(qz_o_mux ^ qx_o_mux ^ qy_o_mux)
        )

        If(qalumode_o_mux[2],
           comux(0),
        ).Else(
            comux(co),
        )
        smux(qalumode_o_mux[3]._ternary(co, s))

        carryout_o_hw = self._sig("carryout_o_hw", Bits(CARRYOUT_W))
        carryout_o_hw[0]((qalumode_o_mux[0] & qalumode_o_mux[1])._ternary(~cout0, cout0))
        carryout_o_hw[1]((qalumode_o_mux[0] & qalumode_o_mux[1])._ternary(~cout1, cout1))
        carryout_o_hw[2]((qalumode_o_mux[0] & qalumode_o_mux[1])._ternary(~cout2, cout2))
        carryout_o_hw[3]((qalumode_o_mux[0] & qalumode_o_mux[1])._ternary(~cout3, cout3))
        alu_o(qalumode_o_mux[1]._ternary(
            ~Concat(s3[12:0], s2[12:0], s1[12:0], s0[12:0]),
             Concat(s3[12:0], s2[12:0], s1[12:0], s0[12:0])
        ))
        carrycascout_o(cout3)
        multsignout_o_opmode((qopmode_o_mux[7:4]._eq(0b100))._ternary(MULTSIGNIN, qmult_o_mux[42]))
        If((qopmode_o_mux[4:0]._eq(0b0101) | (qalumode_o_mux[4:2] != 0b00)),
            carryout_o[3](None),
            carryout_o[2](None),
            carryout_o[1](None),
            carryout_o[0](None),
        ).Else(
            carryout_o[3](carryout_o_hw[3]),
            carryout_o[2](carryout_o_hw[2] if USE_SIMD == "FOUR12" else None),
            carryout_o[1](carryout_o_hw[1] if USE_SIMD in ["TWO24", "FOUR12"] else None),
            carryout_o[0](carryout_o_hw[0] if USE_SIMD == "FOUR12" else None),
        )

        #--########################### END ALU ################################
        #*** CarryIn Mux and Register
        #-------  input 0
        If(clk_in._onRisingEdge(),
            If(RSTALLCARRYIN,
                qcarryin_o_reg0(0b0)
            ).Elif(CECARRYIN,
                qcarryin_o_reg0(carryin_in)
            )
        )
        if CARRYINREG == 0:
            qcarryin_o_mux0(carryin_in)
        elif CARRYINREG == 1:
            qcarryin_o_mux0(qcarryin_o_reg0)
        else:
            raise AssertionError()

        #-------  input 7
        If(clk_in._onRisingEdge(),
            If(RSTALLCARRYIN,
                qcarryin_o_reg7(0b0)
            ).Elif(CEM,
                qcarryin_o_reg7(ad_mult[24]._eq(b_mult[17]))
            )
        )

        if MREG == 0:
            qcarryin_o_mux7(ad_mult[24]._eq(b_mult[17]))
        elif MREG == 1:
            qcarryin_o_mux7(qcarryin_o_reg7)
        else:
            raise ValueError("MREG is set to %d. Legal values for this attribute are 0 or 1.", MREG)

        Switch(qcarryinsel_o_mux)\
            .Case(CARRYIN_SEL.CARRYIN.value,
                qcarryin_o_mux_tmp(qcarryin_o_mux0))\
            .Case(CARRYIN_SEL.PCIN_47_n.value,
                qcarryin_o_mux_tmp(~PCIN[47]))\
            .Case(CARRYIN_SEL.CARRYCASCIN.value,
                qcarryin_o_mux_tmp(CARRYCASCIN))\
            .Case(CARRYIN_SEL.PCIN_47.value,
                qcarryin_o_mux_tmp(PCIN[47]))\
            .Case(CARRYIN_SEL.CARRYCASCOUT.value,
                qcarryin_o_mux_tmp(carrycascout_o_mux))\
            .Case(CARRYIN_SEL.P_47_n.value,
                qcarryin_o_mux_tmp(~qp_o_mux[47]))\
            .Case(CARRYIN_SEL.A_27_eq_B_17.value,
                qcarryin_o_mux_tmp(qcarryin_o_mux7))\
            .Case(CARRYIN_SEL.P_47.value,
                qcarryin_o_mux_tmp(qp_o_mux[47]))

        # disable carryin when performing logic operation
        If(qalumode_o_mux[3] | qalumode_o_mux[2],
            qcarryin_o_mux(0b0)
        ).Else(
            qcarryin_o_mux(qcarryin_o_mux_tmp)
        )

        if AUTORESET_PATDET == "RESET_MATCH":
            the_auto_reset_patdet(pdet_o_reg1)
        elif AUTORESET_PATDET == "RESET_NOT_MATCH":
            the_auto_reset_patdet(pdet_o_reg2 & ~pdet_o_reg1)
        else:
            the_auto_reset_patdet(0)

        #--####################################################################
        #--#####      CARRYOUT, CARRYCASCOUT. MULTSIGNOUT and PCOUT      ######
        #--####################################################################
        #*** register with 1 level of register
        If(clk_in._onRisingEdge(),
            If(RSTP._isOn() | the_auto_reset_patdet._isOn(),
                carryout_o_reg(0b0),
                carrycascout_o_reg(0b0),
                qmultsignout_o_reg(0b0),
                qp_o_reg1(0b0)
            ).Elif(CEP,
                carryout_o_reg(carryout_o),
                carrycascout_o_reg(carrycascout_o),
                qmultsignout_o_reg(multsignout_o_opmode),
                qp_o_reg1(alu_o)
            )
        )
        if PREG == 0:
            carryout_o_mux(carryout_o)
            carrycascout_o_mux(carrycascout_o)
            multsignout_o_mux(multsignout_o_opmode)
            qp_o_mux(alu_o)

        elif PREG == 1:
            carryout_o_mux(carryout_o_reg)
            carrycascout_o_mux(carrycascout_o_reg)
            multsignout_o_mux(qmultsignout_o_reg)
            qp_o_mux(qp_o_reg1)
        else:
            raise AssertionError()

        carryout_x_o(Concat(
            carryout_o_mux[3],
            carryout_o_mux[2] if USE_SIMD == "FOUR12" else BIT.from_py(None),
            carryout_o_mux[1] if USE_SIMD in ["TWO24", "FOUR12"] else BIT.from_py(None),
            carryout_o_mux[0] if USE_SIMD == "FOUR12" else BIT.from_py(None),
        ))

        the_pattern(PATTERN if SEL_PATTERN == "PATTERN" else qc_o_mux)

        # selet mask
        if USE_PATTERN_DETECT == "NO_PATDET":
            the_mask(mask(48))
        elif SEL_MASK == "MASK":
            the_mask(MASK)
        elif SEL_MASK == "C":
            the_mask(qc_o_mux)
        elif SEL_MASK == "ROUNDING_MODE1":
            the_mask(~qc_o_mux << 1)
        elif SEL_MASK == "ROUNDING_MODE2":
            the_mask(~qc_o_mux << 2)
        else:
            raise AssertionError()

        If(opmode_valid_flag,
            pdet_o(And(*(~(the_pattern ^ alu_o) | the_mask))),
            pdetb_o(And(*(the_pattern ^ alu_o | the_mask))),
        ).Else(
            pdet_o(None),
            pdetb_o(None),
        )
        pdet_o_mux(pdet_o_reg1 if PREG == 1 else pdet_o)
        pdetb_o_mux(pdetb_o_reg1 if PREG == 1 else pdetb_o)

        #*** Output register PATTERN DETECT and UNDERFLOW / OVERFLOW
        If(clk_in._onRisingEdge(),
            If(RSTP._isOn() | the_auto_reset_patdet._isOn(),
                pdet_o_reg1(0b0),
                pdet_o_reg2(0b0),
                pdetb_o_reg1(0b0),
                pdetb_o_reg2(0b0)
            ).Elif(CEP,
                pdet_o_reg2(pdet_o_reg1),
                pdet_o_reg1(pdet_o),
                pdetb_o_reg2(pdetb_o_reg1),
                pdetb_o_reg1(pdetb_o)
            )
        )
        if PREG == 1 or USE_PATTERN_DETECT == "PATDET":
            overflow_o(pdet_o_reg2 & ~pdet_o_reg1 & ~pdetb_o_reg1),
            underflow_o(pdetb_o_reg2 & ~pdet_o_reg1 & ~pdetb_o_reg1)
        else:
            overflow_o(None),
            underflow_o(None)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = DSP48E1()
    print("# note that nothing should be printed out because the DSP48E1 has dissabled serialization (because it is part of UNISIM library)")
    print(to_rtl_str(u))
