# JMP_REL = 0
    # accumulator = mem[IP+1]
    # IP = IP + accumulator 
NOP = 0

# set pin (PIN_VDD, PIN_VBAT, PIN_RES, PIN_DC)
PIN_SET = 1
    # pin = ir[7]    

LOAD_DATA = 2  # arg on next addr, (IP +=2)
    # 1) mem[IP+1] 
    # 2) collect to accumulator, IP +=1,

LOAD_ROW = 3
    # accumulator = row

# load row of the bitmap (for char in char_tmp)     
LOAD_BM_ROW = 4
    # 1) charToBm[Concat(temp_char, charBMrow)]
    # 2) wait on data to load
    #    collec data to acumulator, charBMrow+=1

LOAD_EXTERN = 5
    # dataIn.rd = 1, wait for dataIn.vld
    
DO_WAIT = 6  #  time in accumulator [ms]
    # 1) temp_delay = accumulator
    #    temp_delay_en = 1
    # 2) wait for temp_delay_fin
    # 3) temp_delay_en = 0
 
SEND = 7 
    # 1) temp_spi_data = accumulator
    #    temp_spi_en = 1
    # 2) wait for temp_spi_fin
    # 3) temp_spi_en = 0, 
    
STORE_CHAR = 8
    # char_tmp = accumulator
    
COLUMN_INCR = 9
    # if column == COLUMNS - 1:
    #    column=0 
    # else:
    #    column +=1
COLUMN_CLR = 10
    # column = 0

ROW_CLR  = 11
ROW_INCR = 12
    # if row == ROWS -1:
    #     row +=1
    # else:
    #     row = 0

##########################################################################
# pin definitions
PIN_VDD, PIN_VBAT, PIN_RES, PIN_DC = range(4)
    

