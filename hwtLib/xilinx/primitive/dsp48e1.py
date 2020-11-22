from hwt.code import If, Switch, Concat, In, And
from hwt.code_utils import rename_signal
from hwt.hdl.typeShortcuts import hBit, vec
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import  STR, BIT
from hwt.interfaces.std import Signal
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from pyMathBitPrecise.bit_utils import mask, set_bit_range


def replicate(n, v):
    return Concat(*(v for _ in range(n)))


# deassign_xyz_mux;
ARITHMETIC_MODES_DRC_deassign_xyz_mux = [
    # 0bxxx0101010
    * [set_bit_range(0b0000101010, 7, 3, i) for i in range(8)],
    0b0000000000,
    0b0000011000,
    0b0000011010,
    0b0000101000,
    0b0001000000,
    0b0001011000,
    0b0001011010,
    0b0001100000,
    0b0001100010,
    0b0001111000,
    0b0001111010,
    0b0010000000,
    0b0010011000,
    0b0010011001,
    0b0010011011,
    0b0010101000,
    0b0010101001,
    0b0010101011,
    0b0010101110,
    0b0011000000,
    0b0011011000,
    0b0011011001,
    0b0011011011,
    0b0011100000,
    0b0011100001,
    0b0011100011,
    0b0011100100,
    0b0011111000,
    0b0011111001,
    0b0011111011,
    0b0110000000,
    0b0110000010,
    0b0110011000,
    0b0110011010,
    0b0110101000,
    0b0110101110,
    0b0111000000,
    0b0111000010,
    0b0111011000,
    0b0111100000,
    0b0111100010,
    0b0111111000,
    0b1010000000,
    0b1010011000,
    0b1010011001,
    0b1010011011,
    0b1010101000,
    0b1010101001,
    0b1010101011,
    0b1010101110,
    0b1011000000,
    0b1011011000,
    0b1011011001,
    0b1011011011,
    0b1011100000,
    0b1011100001,
    0b1011100011,
    0b1011111000,
    0b1011111001,
    0b1011111011,
]

# if (PREG != 1) display_invalid_opmode; else deassign_xyz_mux;
ARITHMETIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1 = [
    0b0000010000,
    0b0000010010,
    0b0000011100,
    0b0001010000,
    0b0001010010,
    0b0001011100,
    0b0001100100,
    0b0001110000,
    0b0001110010,
    0b0001110101,
    0b0001110111,
    0b0001111100,
    0b0010010000,
    0b0010010101,
    0b0010010111,
    0b0011010000,
    0b0011010101,
    0b0011010111,
    0b0011110000,
    0b0011110101,
    0b0011110111,
    0b0011110001,
    0b0011110011,
    0b0100000000,
    0b0100000010,
    0b0100010000,
    0b0100010010,
    0b0100011000,
    0b0100011010,
    0b0100011101,
    0b0100011111,
    0b0100101000,
    0b0100101101,
    0b0100101111,
    0b0101000000,
    0b0101000010,
    0b0101010000,
    0b0101011000,
    0b0101011101,
    0b0101011111,
    0b0101100000,
    0b0101100010,
    0b0101100101,
    0b0101100111,
    0b0101110000,
    0b0101110101,
    0b0101110111,
    0b0101111000,
    0b0101111101,
    0b0101111111,
    0b0110000100,
    0b0110010000,
    0b0110010010,
    0b0110010101,
    0b0110010111,
    0b0110011100,
    0b0111000100,
    0b0111010000,
    0b0111010101,
    0b0111010111,
    0b0111110000,
    0b1001000010,
    0b1010010000,
    0b1010010101,
    0b1010010111,
    0b1011010000,
    0b1011010101,
    0b1011010111,
    0b1011110000,
    0b1011110101,
    0b1011110111,
    0b1011110001,
    0b1011110011,
    0b1100000000,
    0b1100010000,
    0b1100011000,
    0b1100011101,
    0b1100011111,
    0b1100101000,
    0b1100101101,
    0b1100101111,
    0b1101000000,
    0b1101010000,
    0b1101011000,
    0b1101011101,
    0b1101011111,
    0b1101100000,
    0b1101100101,
    0b1101100111,
    0b1101110000,
    0b1101110101,
    0b1101110111,
    0b1101111000,
    0b1101111101,
    0b1101111111,
]

LOGIC_MODES_DRC_deassign_xyz_mux = [
    0b0000000,
    0b0000011,
    0b0010000,
    0b0010011,
    0b0110000,
    0b0110011,
    0b1010000,
    0b1010011,
    0b0001000,
    0b0001011,
    0b0011000,
    0b0011011,
    0b0111000,
    0b0111011,
    0b1011000,
    0b1011011,
]
LOGIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1 = [
    0b0000010,
    0b0010010,
    0b0100000,
    0b0100010,
    0b0100011,
    0b0110010,
    0b1010010,
    0b1100000,
    0b1100010,
    0b1100011,
    0b0001010,
    0b0011010,
    0b0101000,
    0b0101010,
    0b0101011,
    0b0111010,
    0b1011010,
    0b1101000,
    0b1101010,
    0b1101011,
]


class DSP48E1(Unit):
    """
    https://www.xilinx.com/support/documentation/user_guides/ug479_7Series_DSP48E1.pdf
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
        self.IS_ALUMODE_INVERTED = Param(Bits(4, None).from_py(0b0000))
        self.IS_CARRYIN_INVERTED = Param(BIT.from_py(0b0))
        self.IS_CLK_INVERTED = Param(BIT.from_py(0b0))
        self.IS_INMODE_INVERTED = Param(Bits(5, None).from_py(0b00000))
        self.IS_OPMODE_INVERTED = Param(Bits(7, None).from_py(0b0000000))
        self.MASK = Param(Bits(48, None).from_py(0x3fffffffffff))
        self.MREG = Param(1)
        self.OPMODEREG = Param(1)
        self.PATTERN = Param(Bits(48, None).from_py(0x000000000000))
        self.PREG = Param(1)
        self.SEL_MASK = Param("MASK")
        self.SEL_PATTERN = Param("PATTERN")
        self.USE_DPORT = Param("FALSE")
        self.USE_MULT = Param("MULTIPLY")
        self.USE_PATTERN_DETECT = Param("NO_PATDET")
        self.USE_SIMD = Param("ONE48")

    def deassign_xyz_mux(self):
        """------------------------------------------------------------------
        *** DRC for OPMODE
        ------------------------------------------------------------------
        """
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
        # ports
        self.ACOUT = Signal(Bits(30, None))._m()
        self.BCOUT = Signal(Bits(18, None))._m()
        self.CARRYCASCOUT = Signal(BIT)._m()
        self.CARRYOUT = Signal(Bits(4, None))._m()
        self.MULTSIGNOUT = Signal(BIT)._m()
        self.OVERFLOW = Signal(BIT)._m()
        self.P = Signal(Bits(48, None))._m()
        self.PATTERNBDETECT = Signal(BIT)._m()
        self.PATTERNDETECT = Signal(BIT)._m()
        self.PCOUT = Signal(Bits(48, None))._m()
        self.UNDERFLOW = Signal(BIT)._m()
        self.A = Signal(Bits(30, None))
        self.ACIN = Signal(Bits(30, None))
        self.ALUMODE = Signal(Bits(4, None))
        self.B = Signal(Bits(18, None))
        self.BCIN = Signal(Bits(18, None))
        self.C = Signal(Bits(48, None))
        self.CARRYCASCIN = Signal(BIT)
        self.CARRYIN = Signal(BIT)
        self.CARRYINSEL = Signal(Bits(3, None))
        self.CEA1 = Signal(BIT)
        self.CEA2 = Signal(BIT)
        self.CEAD = Signal(BIT)
        self.CEALUMODE = Signal(BIT)
        self.CEB1 = Signal(BIT)
        self.CEB2 = Signal(BIT)
        self.CEC = Signal(BIT)
        self.CECARRYIN = Signal(BIT)
        self.CECTRL = Signal(BIT)
        self.CED = Signal(BIT)
        self.CEINMODE = Signal(BIT)
        self.CEM = Signal(BIT)
        self.CEP = Signal(BIT)
        self.CLK = Signal(BIT)
        self.D = Signal(Bits(25, None))
        self.INMODE = Signal(Bits(5, None))
        self.MULTSIGNIN = Signal(BIT)
        self.OPMODE = Signal(Bits(7, None))
        self.PCIN = Signal(Bits(48, None))
        self.RSTA = Signal(BIT)
        self.RSTALLCARRYIN = Signal(BIT)
        self.RSTALUMODE = Signal(BIT)
        self.RSTB = Signal(BIT)
        self.RSTC = Signal(BIT)
        self.RSTCTRL = Signal(BIT)
        self.RSTD = Signal(BIT)
        self.RSTINMODE = Signal(BIT)
        self.RSTM = Signal(BIT)
        self.RSTP = Signal(BIT)
        # component instances

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
        # define constants
        MODULE_NAME = STR.from_py("DSP48E1")
        #------------------- constants -------------------------
        MAX_CARRYOUT = 4
        MAX_A = 30
        MAX_ALUMODE = 4
        MAX_A_MULT = 25
        MAX_B = 18
        MAX_B_MULT = 18
        MAX_D = 25
        MAX_INMODE = 5
        MAX_OPMODE = 7
        MAX_ALU_FULL = 48
        MSB_CARRYOUT = MAX_CARRYOUT - 1
        MSB_A = MAX_A - 1
        MSB_ALUMODE = MAX_ALUMODE - 1
        MSB_A_MULT = MAX_A_MULT - 1
        MSB_B = MAX_B - 1
        MSB_B_MULT = MAX_B_MULT - 1
        MSB_D = MAX_D - 1
        MSB_INMODE = MAX_INMODE - 1
        MSB_OPMODE = MAX_OPMODE - 1
        MSB_ALU_FULL = MAX_ALU_FULL - 1

        IS_ALUMODE_INVERTED_BIN = self._sig("IS_ALUMODE_INVERTED_BIN", Bits(4, None), def_val=IS_ALUMODE_INVERTED)
        IS_CARRYIN_INVERTED_BIN = self._sig("IS_CARRYIN_INVERTED_BIN", BIT, def_val=IS_CARRYIN_INVERTED)
        IS_CLK_INVERTED_BIN = self._sig("IS_CLK_INVERTED_BIN", BIT, def_val=IS_CLK_INVERTED)
        IS_INMODE_INVERTED_BIN = self._sig("IS_INMODE_INVERTED_BIN", Bits(5, None), def_val=IS_INMODE_INVERTED)
        IS_OPMODE_INVERTED_BIN = self._sig("IS_OPMODE_INVERTED_BIN", Bits(7, None), def_val=IS_OPMODE_INVERTED)
        a_o_mux = self._sig("a_o_mux", Bits(30, None))
        qa_o_mux = self._sig("qa_o_mux", Bits(30, None))
        qa_o_reg1 = self._sig("qa_o_reg1", Bits(30, None))
        qa_o_reg2 = self._sig("qa_o_reg2", Bits(30, None))
        qacout_o_mux = self._sig("qacout_o_mux", Bits(30, None))
        # new
        qinmode_o_mux = self._sig("qinmode_o_mux", Bits(5, None))
        qinmode_o_reg = self._sig("qinmode_o_reg", Bits(5, None))
        # new
        a_preaddsub = self._sig("a_preaddsub", Bits(25, None))
        b_o_mux = self._sig("b_o_mux", Bits(18, None))
        qb_o_mux = self._sig("qb_o_mux", Bits(18, None))
        qb_o_reg1 = self._sig("qb_o_reg1", Bits(18, None))
        qb_o_reg2 = self._sig("qb_o_reg2", Bits(18, None))
        qbcout_o_mux = self._sig("qbcout_o_mux", Bits(18, None))
        qcarryinsel_o_mux = self._sig("qcarryinsel_o_mux", Bits(3, None))
        qcarryinsel_o_reg1 = self._sig("qcarryinsel_o_reg1", Bits(3, None))
        # new  
        d_o_mux = self._sig("d_o_mux", Bits(MSB_D + 1, None))
        qd_o_mux = self._sig("qd_o_mux", Bits(MSB_D + 1, None))
        qd_o_reg1 = self._sig("qd_o_reg1", Bits(MSB_D + 1, None))
        qmult_o_mux = self._sig("qmult_o_mux", Bits(MSB_A_MULT + MSB_B_MULT + 1 + 1, None))
        qmult_o_reg = self._sig("qmult_o_reg", Bits(MSB_A_MULT + MSB_B_MULT + 1 + 1, None))
        # 42:0
        qc_o_mux = self._sig("qc_o_mux", Bits(48, None))
        qc_o_reg1 = self._sig("qc_o_reg1", Bits(48, None))
        qp_o_mux = self._sig("qp_o_mux", Bits(48, None))
        qp_o_reg1 = self._sig("qp_o_reg1", Bits(48, None))
        qx_o_mux = self._sig("qx_o_mux", Bits(48, None))
        qy_o_mux = self._sig("qy_o_mux", Bits(48, None))
        qz_o_mux = self._sig("qz_o_mux", Bits(48, None))
        qopmode_o_mux = self._sig("qopmode_o_mux", Bits(7, None))
        qopmode_o_reg1 = self._sig("qopmode_o_reg1", Bits(7, None))
        qcarryin_o_mux0 = self._sig("qcarryin_o_mux0", BIT)
        qcarryin_o_reg0 = self._sig("qcarryin_o_reg0", BIT)
        qcarryin_o_mux7 = self._sig("qcarryin_o_mux7", BIT)
        qcarryin_o_reg7 = self._sig("qcarryin_o_reg7", BIT)
        qcarryin_o_mux = self._sig("qcarryin_o_mux", BIT)
        qalumode_o_mux = self._sig("qalumode_o_mux", Bits(4, None))
        qalumode_o_reg1 = self._sig("qalumode_o_reg1", Bits(4, None))
        self.invalid_opmode = invalid_opmode = self._sig("invalid_opmode", BIT, def_val=1)
        self.opmode_valid_flag = opmode_valid_flag = self._sig("opmode_valid_flag", BIT, def_val=1)
        #   reg [47:0] alu_o;
        alu_o = self._sig("alu_o", Bits(48, None))
        qmultsignout_o_reg = self._sig("qmultsignout_o_reg", BIT)
        multsignout_o_mux = self._sig("multsignout_o_mux", BIT)
        multsignout_o_opmode = self._sig("multsignout_o_opmode", BIT)
        pdet_o_mux = self._sig("pdet_o_mux", BIT)
        pdetb_o_mux = self._sig("pdetb_o_mux", BIT)
        the_pattern = self._sig("the_pattern", Bits(48, None))
        the_mask = self._sig("the_mask", Bits(48, None), def_val=0)
        carrycascout_o = self._sig("carrycascout_o", BIT)
        the_auto_reset_patdet = self._sig("the_auto_reset_patdet", BIT)
        carrycascout_o_reg = self._sig("carrycascout_o_reg", BIT, def_val=0)
        carrycascout_o_mux = self._sig("carrycascout_o_mux", BIT, def_val=0)

        # CR 588861
        carryout_o_reg = self._sig("carryout_o_reg", Bits(4, None), def_val=0)
        carryout_o_mux = self._sig("carryout_o_mux", Bits(4, None))
        carryout_x_o = self._sig("carryout_x_o", Bits(4, None))
        pdet_o = self._sig("pdet_o", BIT)
        pdetb_o = self._sig("pdetb_o", BIT)
        pdet_o_reg1 = self._sig("pdet_o_reg1", BIT)
        pdet_o_reg2 = self._sig("pdet_o_reg2", BIT)
        pdetb_o_reg1 = self._sig("pdetb_o_reg1", BIT)
        pdetb_o_reg2 = self._sig("pdetb_o_reg2", BIT)
        overflow_o = self._sig("overflow_o", BIT)
        underflow_o = self._sig("underflow_o", BIT)
        mult_o = self._sig("mult_o", Bits(MSB_A_MULT + MSB_B_MULT + 1 + 1, None))
        #   reg [(MSB_A_MULT+MSB_B_MULT+1):0] mult_o;  // 42:0
        # new 
        ad_addsub = self._sig("ad_addsub", Bits(MSB_A_MULT + 1, None))
        ad_mult = self._sig("ad_mult", Bits(MSB_A_MULT + 1, None))
        qad_o_reg1 = self._sig("qad_o_reg1", Bits(MSB_A_MULT + 1, None))
        qad_o_mux = self._sig("qad_o_mux", Bits(MSB_A_MULT + 1, None))
        b_mult = self._sig("b_mult", Bits(MSB_B_MULT + 1, None))
        # cci_drc_msg = self._sig("cci_drc_msg", BIT, def_val=0b0)
        # cis_drc_msg = self._sig("cis_drc_msg", BIT, def_val=0b0)
        opmode_in = self._sig("opmode_in", Bits(MSB_OPMODE + 1, None))
        alumode_in = self._sig("alumode_in", Bits(MSB_ALUMODE + 1, None))
        carryin_in = self._sig("carryin_in", BIT)
        clk_in = self._sig("clk_in", BIT)
        inmode_in = self._sig("inmode_in", Bits(MSB_INMODE + 1, None))
        #*** Y mux
        # 08-06-08  
        # IR 478378
        y_mac_cascd = rename_signal(self, qopmode_o_mux[slice(7, 4)]._eq(0b100)._ternary(replicate(48, MULTSIGNIN), Bits(48, None).from_py(mask(48))), "y_mac_cascd")
        #--####################################################################
        #--#####                         ALU                              #####
        #--####################################################################
        co = self._sig("co", Bits(MSB_ALU_FULL + 1, None))
        s = self._sig("s", Bits(MSB_ALU_FULL + 1, None))
        comux = self._sig("comux", Bits(MSB_ALU_FULL + 1, None))
        smux = self._sig("smux", Bits(MSB_ALU_FULL + 1, None))
        carryout_o_hw = self._sig("carryout_o_hw", Bits(MSB_CARRYOUT + 1, None))
        carryout_o = self._sig("carryout_o", Bits(MSB_CARRYOUT + 1, None))
        # FINAL ADDER
        s0 = rename_signal(self, Concat(hBit(0), comux[slice(11, 0)], qcarryin_o_mux) + Concat(hBit(0), smux[slice(12, 0)]), "s0")
        cout0 = rename_signal(self, comux[11] + s0[12], "cout0")
        C1 = rename_signal(self, hBit(0b0) if USE_SIMD == "FOUR12" else s0[12], "C1")
        co11_lsb = rename_signal(self, hBit(0b0) if USE_SIMD == "FOUR12" else comux[11], "co11_lsb")
        s1 = rename_signal(self, Concat(hBit(0), comux[slice(23, 12)], co11_lsb) + Concat(hBit(0), smux[slice(24, 12)]) + Concat(vec(0, 12), C1), "s1")
        cout1 = rename_signal(self, comux[23] + s1[12], "cout1")
        C2 = rename_signal(self, hBit(0b0) if (USE_SIMD in ["TWO24", "FOUR12"]) else s1[12], "C2")
        co23_lsb = rename_signal(self, hBit(0b0) if (USE_SIMD in ["TWO24", "FOUR12"]) else comux[23], "co23_lsb")
        s2 = rename_signal(self, Concat(hBit(0), comux[slice(35, 24)], co23_lsb) + Concat(hBit(0), smux[slice(36, 24)]) + Concat(vec(0, 12), C2), "s2")
        cout2 = rename_signal(self, comux[35] + s2[12], "cout2")
        C3 = rename_signal(self, hBit(0b0) if  USE_SIMD == "FOUR12" else s2[12], "C3")
        co35_lsb = rename_signal(self, hBit(0b0) if  USE_SIMD == "FOUR12" else comux[35], "co35_lsb")
        s3 = rename_signal(self, Concat(hBit(0), comux[slice(48, 36)], co35_lsb) + Concat(vec(0, 2), smux[slice(48, 36)]) + Concat(vec(0, 13), C3), "s3")
        cout3 = rename_signal(self, s3[12], "cout3")
        cout4 = rename_signal(self, s3[13], "cout4")
        qcarryin_o_mux_tmp = self._sig("qcarryin_o_mux_tmp", BIT)

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

        #-------- A_INPUT check
        if A_INPUT not in ("DIRECT", "CASCADE"):
            raise ValueError("The attribute A_INPUT on DSP48E1 instance %m is set to %s.  Legal values for this attribute are DIRECT or CASCADE.", A_INPUT)
        #-------- ALUMODEREG check
        if ALUMODEREG not in (0, 1):
            raise ValueError("The attribute ALUMODEREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", ALUMODEREG)
        #-------- AREG check
        if AREG not in (0, 1, 2):
            raise ValueError("The attribute AREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1 or 2.", AREG)
        #-------- (ACASCREG) and (ACASCREG vs AREG) check
        if AREG in (0, 1):
            if AREG != ACASCREG:
                raise ValueError("The attribute ACASCREG  on DSP48E1 instance %m is set to %d.  ACASCREG has to be set to same value as AREG attribute.", ACASCREG)
        elif AREG == 2:
            if AREG != ACASCREG and AREG - 1 != ACASCREG:
                raise ValueError("The attribute ACASCREG  on DSP48E1 instance %m is set to %d.  ACASCREG has to be set to either 2 or 1 when attribute AREG = 2.", ACASCREG)
        else:
            raise ValueError(AREG)

        #-------- B_INPUT check
        if B_INPUT not in ("DIRECT", "CASCADE"):
            raise ValueError("The attribute B_INPUT on DSP48E1 instance %m is set to %s.  Legal values for this attribute are DIRECT or CASCADE.", B_INPUT)

        #-------- BREG check
        if BREG not in (0, 1, 2):
            raise ValueError("The attribute BREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1 or 2.", BREG)

        #-------- (BCASCREG) and (BCASCREG vs BREG) check
        if BREG in (0, 1):
            if BREG != BCASCREG:
                raise ValueError("The attribute BCASCREG  on DSP48E1 instance %m is set to %d.  BCASCREG has to be set to same value as BREG.", BCASCREG)
        elif BREG == 2:
            if BREG != BCASCREG and BREG - 1 != BCASCREG:
                raise ValueError("The attribute BCASCREG  on DSP48E1 instance %m is set to %d.  BCASCREG has to be set to either 2 or 1 when attribute BREG = 2.", BCASCREG)
        else:
            raise ValueError(BREG)
        #-------- CARRYINREG check
        if CARRYINREG not in (0, 1):
            raise ValueError("The attribute CARRYINREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", CARRYINREG)
        #-------- CARRYINSELREG check
        if CARRYINSELREG not in (0, 1):
            raise ValueError("The attribute CARRYINSELREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", CARRYINSELREG)

        #-------- CREG check
        if CREG not in (0, 1):
            raise ValueError("The attribute CREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, or 1.", CREG)

        #-------- OPMODEREG check
        if OPMODEREG not in (0, 1):
            raise ValueError("The attribute OPMODEREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", OPMODEREG)

        #-------- USE_MULT
        if USE_MULT not in ("NONE", "MULTIPLY", "DYNAMIC"):
            raise ValueError("The attribute USE_MULT on DSP48E1 instance %m is set to %s. Legal values for this attribute are MULTIPLY, DYNAMIC or NONE.", USE_MULT)
 
        #-------- USE_PATTERN_DETECT
        if USE_PATTERN_DETECT not in ("PATDET", "NO_PATDET"):
            raise ValueError("The attribute USE_PATTERN_DETECT on DSP48E1 instance %m is set to %s.  Legal values for this attribute are PATDET or NO_PATDET.", USE_PATTERN_DETECT)
        #-------- AUTORESET_PATDET check
        if AUTORESET_PATDET not in ("NO_RESET", "RESET_MATCH", "RESET_NOT_MATCH"):
            raise ValueError("The attribute AUTORESET_PATDET on DSP48E1 instance %m is set to %s.  Legal values for this attribute are  NO_RESET or RESET_MATCH or RESET_NOT_MATCH.", AUTORESET_PATDET)
        #-------- SEL_PATTERN check
        if SEL_PATTERN not in ("PATTERN", "C"):
            raise ValueError("The attribute SEL_PATTERN on DSP48E1 instance %m is set to %s.  Legal values for this attribute are PATTERN or C.", SEL_PATTERN)

        #-------- SEL_MASK check
        if SEL_MASK not in ("MASK", "C", "ROUNDING_MODE1", "ROUNDING_MODE2"):
            raise ValueError("The attribute SEL_MASK on DSP48E1 instance %m is set to %s.  Legal values for this attribute are MASK or C or ROUNDING_MODE1 or ROUNDING_MODE2.", SEL_MASK)

        #-------- MREG check
        if MREG not in (0, 1):
            raise ValueError("The attribute MREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", MREG)

        #-------- PREG check
        if PREG not in (0, 1):
            raise ValueError("The attribute PREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", PREG)

        #*/*********************************************************
        #***  new attribute DRC
        #*********************************************************
        #-------- ADREG check
        if ADREG not in (0, 1):
            raise ValueError("The attribute ADREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", ADREG)

        #-------- DREG check
        if DREG not in (0, 1):
            raise ValueError("The attribute DREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", DREG)

        #-------- INMODEREG check
        if INMODEREG not in (0, 1):
            raise ValueError("The attribute INMODEREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0, 1.", INMODEREG)

        #-------- USE_DPORT
        if USE_DPORT not in ("TRUE", "FALSE"):
            raise ValueError("The attribute USE_DPORT on DSP48E1 instance %m is set to %s.  Legal values for this attribute are TRUE or FALSE.", USE_DPORT)

        if USE_MULT == "NONE" and MREG != 0:
            raise ValueError("Error : [Unisim %s-10] : Attribute USE_MULT is set to \"NONE\" and MREG is set to %2d. MREG must be set to 0 when the multiplier is not used. Instance %m", MODULE_NAME, MREG)

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

        if AREG == 1:
            If(clk_in._onRisingEdge(),
                If(RSTA,
                    qa_o_reg1(0b0),
                    qa_o_reg2(0b0)
                ).Else(
                    If(CEA1,
                        qa_o_reg1(a_o_mux)
                    ),
                    If(CEA2,
                        qa_o_reg2(a_o_mux)
                    )
                )
            )

        elif AREG == 2:
            If(clk_in._onRisingEdge(),
                If(RSTA,
                    qa_o_reg1(0b0),
                    qa_o_reg2(0b0)
                ).Else(
                    If(CEA1,
                        qa_o_reg1(a_o_mux)
                    ),
                    If(CEA2,
                        qa_o_reg2(qa_o_reg1)
                    )
                )
            )
        else:
            raise AssertionError()

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
            a_preaddsub(qa_o_reg1[slice(25, 0)]),
        ).Else(
            a_preaddsub(qa_o_mux[slice(25, 0)]),
        )
        if B_INPUT == "DIRECT":
            b_o_mux(B)
        elif B_INPUT == "CASCADE":
            b_o_mux(BCIN)
        else:
            raise AssertionError()    

        if BREG == 1:
            If(clk_in._onRisingEdge(),
                If(RSTB,
                    qb_o_reg1(0b0),
                    qb_o_reg2(0b0)
                ).Else(
                    If(CEB1,
                        qb_o_reg1(b_o_mux)
                    ),
                    If(CEB2,
                        qb_o_reg2(b_o_mux)
                    )
                )
            )
        elif BREG == 2:
            If(clk_in._onRisingEdge(),
                If(RSTB,
                    qb_o_reg1(0b0),
                    qb_o_reg2(0b0)
                ).Else(
                    If(CEB1,
                        qb_o_reg1(b_o_mux)
                    ),
                    If(CEB2,
                        qb_o_reg2(qb_o_reg1)
                    )
                )
            )
        else:
            raise AssertionError()

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

        ad_addsub(qinmode_o_mux[3]._ternary(-a_preaddsub + qinmode_o_mux[2]._ternary(qd_o_mux, 0b0), a_preaddsub + qinmode_o_mux[2]._ternary(qd_o_mux, 0b0)))

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
                mult_o(replicate(18, ad_mult[24])._concat(ad_mult[slice(25, 0)]) * 
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
        Switch(qopmode_o_mux[slice(2, 0)])\
            .Case(0b00,
                qx_o_mux(0b0))\
            .Case(0b01,
                qx_o_mux(replicate(5, qmult_o_mux[MSB_A_MULT + MSB_B_MULT + 1])._concat(qmult_o_mux)))\
            .Case(0b10,
                qx_o_mux(qp_o_mux))\
            .Case(0b11,
                qx_o_mux(None) 
                if USE_MULT == "MULTIPLY" and (
                    (AREG == 0 and BREG == 0 and MREG == 0) or
                    (AREG == 0 and BREG == 0 and PREG == 0) or
                    (MREG == 0 and PREG == 0))
                # print("OPMODE Input Warning : The OPMODE[1:0] %b to DSP48E1 instance %m is invalid when using attributes USE_MULT = MULTIPLY at %.3f ns. Please set USE_MULT to either NONE or DYNAMIC.", qopmode_o_mux[slice(2, 0)], sim.now // 1000.000000)
                else qx_o_mux(qa_o_mux[slice(MSB_A + 1, 0)]._concat(qb_o_mux[slice(MSB_B + 1, 0)]))
            )

        # add post 2014.4 
        Switch(qopmode_o_mux[slice(4, 2)])\
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
        Switch(qopmode_o_mux[slice(7, 4)])\
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
                qz_o_mux(replicate(17, PCIN[47])._concat(PCIN[slice(48, 17)])))\
            .Case(0b110,
                qz_o_mux(replicate(17, qp_o_mux[47])._concat(qp_o_mux[slice(48, 17)])))\
            .Case(0b111,
                qz_o_mux(replicate(17, qp_o_mux[47])._concat(qp_o_mux[slice(48, 17)])))

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
        #    If(~((qopmode_o_mux[slice(4, 0)] != 0b0101)._isOn())._isOn(),
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
        Switch(qalumode_o_mux[slice(4, 2)])\
            .Case(0b00,
                # -- ARITHMETIC MODES DRC
                If(In(arith_mode_tmp, ARITHMETIC_MODES_DRC_deassign_xyz_mux),
                    self.deassign_xyz_mux()
                ).Elif(In(arith_mode_tmp, ARITHMETIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1),
                    deassign_xyz_mux_if_PREG_eq_1()
                ).Else(
                    # CR 444150
                    # If(qopmode_o_mux._concat(qcarryinsel_o_mux)._eq(0b0000000010)._isOn() & (OPMODEREG._eq(1)._isOn() & CARRYINSELREG._eq(0)._isOn())._isOn(),
                    #    print("DRC warning : The attribute CARRYINSELREG on DSP48E1 instance %m is set to %d. It is required to have CARRYINSELREG be set to 1 to match OPMODEREG, in order to ensure that the simulation model will match the hardware behavior in all use cases.", CARRYINSELREG)
                    # ),
                    # print("OPMODE Input Warning : The OPMODE %b to DSP48E1 instance %m is either invalid or the CARRYINSEL %b for that specific OPMODE is invalid at %.3f ns. This warning may be due to a mismatch in the OPMODEREG and CARRYINSELREG attribute settings. It is recommended that OPMODEREG and CARRYINSELREG always be set to the same value. ", qopmode_o_mux, qcarryinsel_o_mux, sim.now // 1000.000000)
                )
            )\
            .Case(0b01,
               DCR_check_logic_modes() 
            )\
            .Case(0b11,
               DCR_check_logic_modes() 
            ) \
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
        carryout_o_hw[0]((qalumode_o_mux[0] & qalumode_o_mux[1])._ternary(~cout0, cout0))
        carryout_o_hw[1]((qalumode_o_mux[0] & qalumode_o_mux[1])._ternary(~cout1, cout1))
        carryout_o_hw[2]((qalumode_o_mux[0] & qalumode_o_mux[1])._ternary(~cout2, cout2))
        carryout_o_hw[3]((qalumode_o_mux[0] & qalumode_o_mux[1])._ternary(~cout3, cout3))
        alu_o(qalumode_o_mux[1]._ternary(~s3[slice(12, 0)]._concat(s2[slice(12, 0)])._concat(s1[slice(12, 0)])._concat(s0[slice(12, 0)]), s3[slice(12, 0)]._concat(s2[slice(12, 0)])._concat(s1[slice(12, 0)])._concat(s0[slice(12, 0)])))
        carrycascout_o(cout3)
        multsignout_o_opmode((qopmode_o_mux[slice(7, 4)]._eq(0b100))._ternary(MULTSIGNIN, qmult_o_mux[42]))
        If((qopmode_o_mux[slice(4, 0)]._eq(0b0101) | (qalumode_o_mux[slice(4, 2)] != 0b00)),
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
            raise ValueError("The attribute MREG on DSP48E1 instance %m is set to %d.  Legal values for this attribute are 0 or 1.", MREG)

        Switch(qcarryinsel_o_mux)\
            .Case(0b000,
                qcarryin_o_mux_tmp(qcarryin_o_mux0))\
            .Case(0b001,
                qcarryin_o_mux_tmp(~PCIN[47]))\
            .Case(0b010,
                qcarryin_o_mux_tmp(CARRYCASCIN))\
            .Case(0b011,
                qcarryin_o_mux_tmp(PCIN[47]))\
            .Case(0b100,
                qcarryin_o_mux_tmp(carrycascout_o_mux))\
            .Case(0b101,
                qcarryin_o_mux_tmp(~qp_o_mux[47]))\
            .Case(0b110,
                qcarryin_o_mux_tmp(qcarryin_o_mux7))\
            .Case(0b111,
                qcarryin_o_mux_tmp(qp_o_mux[47]))

        # disable carryin when performing logic operation
        If(qalumode_o_mux[3] | qalumode_o_mux[2],
           qcarryin_o_mux(0b0)
        ).Else(
            qcarryin_o_mux(qcarryin_o_mux_tmp)
        )

        the_auto_reset_patdet(
            (pdet_o_reg1 & (AUTORESET_PATDET == "RESET_MATCH")) | 
            (pdet_o_reg2 & (AUTORESET_PATDET == "RESET_NOT_MATCH") & ~pdet_o_reg1)
        )

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
            carryout_o_mux[2] if USE_SIMD == "FOUR12" else hBit(None),
            carryout_o_mux[1] if USE_SIMD in ["TWO24", "FOUR12"] else hBit(None),
            carryout_o_mux[0] if USE_SIMD == "FOUR12" else hBit(None),
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
    print(to_rtl_str(u))
