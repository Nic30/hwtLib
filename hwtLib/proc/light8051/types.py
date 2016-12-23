# Internal state machine states. They are defined here so that they are visible
# to the logging functions in the tb package.
from hwt.hdlObjects.types.enum import Enum
t_cpu_state = Enum("t_cpu_state", [
    "reset_0",                    

    # Fetch & decode #######################-
    "fetch_0",                    # pc in code_addr
    "fetch_1",                    # opcode in code_rd
    "decode_0",                   # microcode in BRAM output
    
    # States for interrupt handling
    "irq_1",                      # SP++, Addr := irq_vector
    "irq_2",                      # SP++, RAM[AB]  := low(PC), AB := SP
    "irq_3",                      # RAM[AB]  := high(PC), AB := SP
    "irq_4",                      # long_jump

    # States for LJMP
    "fetch_addr_0",               # Addr(L) := CODE
    "fetch_addr_1",               # Addr(H) := CODE
    "fetch_addr_0_ajmp",          # Addr(L) := CODE, Addr(H) := PC(H)|OPCODE
    "long_jump",                  # Do actual jump
    
    # States for relative jump instructions 
    "load_rel",                   #
    "rel_jump",
    
    # States for MUL & DIV
    "alu_mul_0",
    "alu_div_0",
    
    # States for CJNE 
    "cjne_a_imm_0",               # T <- #imm
    "cjne_a_imm_1",               # byte1_reg <- rel
    "cjne_a_imm_2",               # do rel jump

    "cjne_ri_imm_0",              # AB,AR    := <Rx>
    "cjne_ri_imm_1",              # AR       := RAM[AB]
    "cjne_ri_imm_2",              # AB       := AR   
    "cjne_ri_imm_3",              # V        := RAM[AB], T := CODE
    "cjne_ri_imm_4",              # byte1_reg <- rel
    "cjne_ri_imm_5",              # do rel jump
    
    "cjne_a_dir_0",               # code_to_ab
    "cjne_a_dir_1",               # ram_to_t
    "cjne_a_dir_2",               # byte1_reg <- rel
    "cjne_a_dir_3",               # do rel jump
    
    "cjne_rn_imm_0",              # AB,AR    := <Rx>
    "cjne_rn_imm_1",              # V        := RAM[AR], T := CODE  
    "cjne_rn_imm_2",              # addr0_reg <- code
    "cjne_rn_imm_3",              # do rel jump

    # States for MOVC instructions 
    "movc_pc_0",
    "movc_dptr_0",
    "movc_1",
    
    # States for ACALL & LCALL instructions
    "acall_0",                    # SP++, Addr(L) := CODE, Addr(H) := PC(H)|OPCODE    
    "acall_1",                    # RAM[AB]  := low(PC), AB := SP, SP++
    "acall_2",                    # RAM[AB]  := high(PC), AB := SP
    # continues at long_jump
    
    "lcall_0",                    # Addr(L) := CODE
    "lcall_1",                    # SP++, Addr(H) := CODE
    "lcall_2",                    # SP++, RAM[AB]  := low(PC), AB := SP
    "lcall_3",                    # RAM[AB]  := high(PC), AB := SP
    "lcall_4",                    # long_jump
    
    # States for JMP @A+DPTR
    "jmp_adptr_0",                # long jump with A+DPTR as target
    
    # States for RET, RETI
    "ret_0",                      # Addr(H)  := RAM[B], SP#, AR,AB := SP
    "ret_1",                      # Addr(L)  := RAM[B], SP#, AR,AB := SP
    "ret_2",                      # long_jump    
    "ret_3",    
    
    # States for DJNZ Rn
    "djnz_rn_0",
    
    # States for DJNZ dir
    # From djnz_dir_1 onwards, they are common to DJNZ Rn; 
    # TODO should rename common states
    "djnz_dir_0",                 # addr0_reg <- dir
    "djnz_dir_1",                 # T <- [dir]
    "djnz_dir_2",                 # [dir] <- alu result, 
    "djnz_dir_3",                 # addr0_reg <- code
    "djnz_dir_4",                 # do rel jump

    # States for special instructions line INC DPTR.
    "special_0",                  # Do special deed
    
    # States for MOV DPTR, #imm16
    "mov_dptr_0",                 # T        := CODE
    "mov_dptr_1",                 # T        := CODE, DPH := T
    "mov_dptr_2",                 # DPL      := T
    
    # States for XCH instructions 
    "xch_dir_0",                  # AB,AR    := CODE
    "xch_rn_0",                   # AB,AR    := <Rx>
    "xch_rx_0",                   # AB,AR    := <Rx>
    "xch_rx_1",                   # AB,AR    := RAM[AB]
    "xch_1",                      # T        := RAM[AB]
    "xch_2",                      # RAM[AB]  := ALU (A,0)
    "xch_3",                      # A        := ALU (T,0)
    
    # States for MOVX A,@Ri and MOVX @Ri,A
    "movx_a_ri_0",
    "movx_a_ri_1",
    "movx_a_ri_2",
    "movx_a_ri_3",
    
    "movx_ri_a_0",
    "movx_ri_a_1",
    "movx_ri_a_2",
    "movx_ri_a_3",
    "movx_ri_a_4",
    
    # states for MOVX A,@DPTR and MOVX @DPTR,A
    "movx_dptr_a_0",
    "movx_a_dptr_0",
    
    # States for JBC, JB and JNB: bit-testing relative jumps
    "jrb_bit_0",                  # AB,AR    := bit<CODE>
    "jrb_bit_1",                  # T        := RAM[AB]
    "jrb_bit_2",                  # RAM[AR]  := ALU_BIT
    "jrb_bit_3",                  # addr0_reg <- code
    "jrb_bit_4",                  # do rel jump
    
    # States for BIT instructions (CPL, CLR, SETB)
    "bit_op_0",                   # AB,AR    := bit<CODE>
    "bit_op_1",                   # T        := RAM[AB]
    "bit_op_2",                   # RAM[AR]  := ALU_BIT
    
    # States for PUSH and POP 
    "push_0",                     # AB       := CODE
    "push_1",                     # T        := RAM[AB], SP++
    "push_2",                     # RAM[AB]  := ALU, AB := SP
    
    "pop_0",                      # AB       := SP
    "pop_1",                      # T        := RAM[B], SP#, AR,AB := CODE
    "pop_2",                      # RAM[AR]  := T
    
    # States for DA A
    "alu_daa_0",                  # 1st stage of DA operation (low nibble)
    "alu_daa_1",                  # 2nd stage of DA operation (high nibble)
    
   
    # States for XCHD A,@Ri
    "alu_xchd_0",                 # AB,AR    := <Rx>
    "alu_xchd_1",                 # AR       := RAM[AB]
    "alu_xchd_2",                 # AB       := AR
    "alu_xchd_3",                 # T        := RAM[AB]
    "alu_xchd_4",                 # RAM[AB]  := ALU
    "alu_xchd_5",                 # A        := ALU'
    
    # States used to fetch operands and store result of ALU class instructions 
    "alu_rx_to_ab",               # AB,AR    := <Rx>
    "alu_ram_to_ar",              # AR       := RAM[AB]
    "alu_ar_to_ab",               # AB       := AR
    "alu_ram_to_t",               # T        := RAM[AB]
    "alu_res_to_a",               # A        := ALU
    "alu_ram_to_t_code_to_ab",    # T        := RAM[AR], AB,AR := CODE 
    "alu_res_to_ram",             # RAM[AB]  := ALU
    "alu_code_to_ab",             # AB,AR    := CODE
    "alu_ram_to_t_rx_to_ab",      # T        := RAM[AR], AB,AR := <Rx> 
    "alu_ram_to_ar_2",            # AR       := RAM[AB]    
    "alu_res_to_ram_ar_to_ab",    # RAM[AB]  := ALU,     AB := AR
    "alu_res_to_ram_code_to_ab",  # RAM[AB]  := ALU,     AB := CODE
    "alu_code_to_t",              # T        := CODE
    "alu_ram_to_v_code_to_t",     # V        := RAM[AR], T := CODE 
    "alu_code_to_t_rx_to_ab",     # T        := CODE,    AB,AR := <Rx>
    
    # States used to fetch operands and store result os BIT class instructions
    "bit_res_to_c",               # C        := BIT_ALU
    
    # Other states ########################-

    "bug_bad_addressing_mode",    # Bad field in microcode word
    "bug_bad_opcode_class",       # Bad field in microcode word
    "state_machine_derailed"      # State machine entered invalid state
    ])