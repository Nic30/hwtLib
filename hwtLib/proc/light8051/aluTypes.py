from hwt.hdlObjects.typeShortcuts import vecT
t_alu_op_sel = vecT(4, False)
t_alu_fns = vecT(6, False)

class AI():
    "alu instruction"
    A_T = 0b0101
    T_0 = 0
    V_T = 0b1001
    A_0 = 0b0100