#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import In, Concat, c, If, Switch
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.proc.light8051.aluTypes import AI, t_alu_op_sel, t_alu_fns 
from hwtLib.proc.light8051.types import t_cpu_state


def carry_stage(sub, a_in, b_in, outp):
    concated = Concat(sub, a_in, b_in, outp)
    return In(concated, [0b0010, 0b0100, 0b0110, 0b0111,
                         0b1001, 0b1010, 0b1011, 0b1101,
                         0b1111])

class Alu(Unit):
    """
    [TODO] not finished
    """
    def _config(self):
        self.IMPLEMENT_BCD_INSTRUCTIONS = Param(False)
        # When true, instructions DA and XCHD will work as in the original MCS51.
        # When false, those instructions will work as NOP, saving some logic.
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        word_t = self.w_t = vecT(self.DATA_WIDTH)
        addClkRstn(self)
        self.result = Signal(dtype=word_t)
        self.nobit_result = Signal(dtype=word_t)
        
        self.xdata_wr = Signal(dtype=word_t)
        self.xdata_rd = Signal(dtype=word_t)
        
        self.iram_sfr_rd = Signal(dtype=word_t)
        self.code_rd = Signal(dtype=word_t)
        self.ACC = Signal(dtype=word_t)
        self.B = Signal(dtype=word_t)
        
        self.cy_in = Signal()
        self.ac_in = Signal()
        
        self.result_is_zero = Signal()
        self.acc_is_zero = Signal()
        self.cy_out = Signal()
        self.ov_out = Signal()
        self.p_out = Signal()
        self.op_sel = Signal(dtype=t_alu_op_sel)
        
        
        self.alu_fn_reg = Signal(dtype=t_alu_fns)
        self.bit_index_reg = Signal(dtype=vecT(3, False))
        self.load_acc_sfr = Signal()
        self.load_acc_out = Signal()
        self.bit_input_out = Signal()
        self.ac_out = Signal()

        self.load_b_sfr = Signal()
        self.mul_ready = Signal()
        self.div_ready = Signal()

        self.use_bitfield = Signal()
        
        self.ps = Signal(dtype=t_cpu_state)
    
    def parity(self, load_acc, acc_input):
        # Parity logic.
        # Note that these intermediate signals will be optimized away; the parity logic
        # will take the equivalent of 3 4-input LUTs.
        parity_4 = acc_input[8:4] ^ acc_input[4:]
        
        parity_2 = parity_4[4:2] ^ parity_4[2:0]
        P_flag_reg = self._reg("P_flag_reg", defVal=0)
        If(load_acc,
            P_flag_reg ** (parity_2[1] ^ parity_2[0])
        )
        self.p_out ** P_flag_reg
    
    def opResolve(self, A_reg, V_reg, T_reg):
        alu_op_sel = self._sig("alu_op_sel", dtype=t_alu_op_sel)
        # ALU input operand mux control. All instructions that use the ALU shall
        # have a say in this logic through the state machine register.
        ps = self.ps
        t = t_cpu_state
        If(In(ps, [t.cjne_a_imm_1, t.cjne_a_dir_2, t.alu_xchd_4, t.alu_xchd_5]),
           alu_op_sel ** AI.A_T 
           
        ).Elif(In(ps, [t.cjne_ri_imm_4, t.cjne_rn_imm_2]),
            alu_op_sel ** AI.V_T 
            
        ).Elif(In(ps, [t.djnz_dir_2, t.djnz_dir_3, t.push_2,
                       t.mov_dptr_1, t.mov_dptr_2, t.xch_3]),
            alu_op_sel ** AI.T_0 
            
        ).Elif(ps._eq(t.xch_2),
            alu_op_sel ** AI.A_0 
            
        ).Else(
            alu_op_sel ** self.op_sel
        )
        
        alu_op_0 = self._sig("alu_op_0", self.w_t)
        # ALU input operand multiplexor: OP0 can be A, V or T.
        Switch(alu_op_sel[4:2])\
        .Case(0b01,
            alu_op_0 ** A_reg 
        ).Case(0b10,
            alu_op_0 ** V_reg 
        ).Default(
            alu_op_0 ** T_reg
        )
        
        alu_op_1 = self._sig("alu_op_1", self.w_t)
        Switch(alu_op_sel[2:])\
        .Case(0b01,
            alu_op_1 ** T_reg 
        ).Default(
            alu_op_1 ** 0 
        )
    
    def logicOps(self, op0, op1, ctrl):
        # ALU: logic operations (1-LUT deep)
        res = self._sig("alu_logic_result", self.w_t)
        Switch(ctrl)\
        .Case(0,
            res ** (op0 & op1)
        ).Case(1,
            res ** (op0 | op1)
        ).Case(2,
            res ** (op0 ^ op1)
        ).Default(
            res ** ~op0   
        )
        
        return res

    def swapOps(self, logicRes, alu_ctrl_mux_2):
        # ALU: SWAP logic; operates on logic result
        res = self._sig("alu_swap_result", self.w_t)
        If(alu_ctrl_mux_2,
           c(Concat(logicRes[:4], logicRes[4:]), res)
        ).Else(
            c(logicRes, res)
        )
        return res

    def shiftOps(self, op0, cy_in, ctrl):
        # ALU: shift operations
        res = self._sig("alu_shift_result", self.w_t)
        Switch(ctrl)\
        .Case(0,  # RR
            c(op0[0]._concat(op0[8:1]), res)
        ).Case(1,  # RRC
            c(cy_in._concat(op0[8:1]), res)
        ).Case(2,  # RL
            c(op0[7:0]._concat(op0[7]), res)   
        ).Default(# RLC
            c(op0[7:0]._concat(cy_in), res)
        )
        return res
        
    
    def dataPath(self, A_reg, V_reg, T_reg):
        # Datapath: ALU and ALU operand multiplexors --------------------------------
        raise NotImplementedError()
        
        

        
    def _impl(self):
        raise NotImplementedError()
        # Extract the ALU control bits from the decoded ALU operation code.
        # First the function selector code...
        #alu_ctrl_fn_arith = alu_fn_reg[6:3]
        #alu_ctrl_fn_logic = alu_fn_reg[5:3]
        #alu_ctrl_fn_shift = alu_fn_reg[5:3]
        ## ...then the multiplexor control bits.
        #alu_ctrl_mux_2 = alu_fn_reg[2]
        #alu_ctrl_mux_1 = alu_fn_reg[1]
        #alu_ctrl_mux_0 = alu_fn_reg[0]
        #
        #
        #acc_is_zero = A_reg._eq(0)
        #c(A_reg, self.ACC, self.xdata_wr)
