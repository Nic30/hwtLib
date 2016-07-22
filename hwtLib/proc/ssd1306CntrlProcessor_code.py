def sendControlls(controllData):
    code = []
    for c in controllData:
        code.extend([LOAD, c, SEND_CONTROLL])
    return code

JMP_REL = 0
    # accumulator = mem[IP+1]
    # IP = IP + accumulator 
    
OLED_ON = 1
    # temp_dc <= 0
    # temp_vdd <= 1'b0;

OLED_ON_FINALIZE = 2
    # temp_vbat = 0
    # load 100
    # temp_res = 0
    # load 100
    # temp_res = 1

LOAD = 2  # arg on next addr, (IP +=2)
    # accumulator = mem[IP+1], IP +=2,
     
LOAD_PAGECNTR = 3
# load row of the bitmap (for char in char_tmp)

LOAD_BM_ROW = 4 # arg = index of row
    # set temp_addr
    # wait on data to load
    # collec data to acumulator
LOAD_EXTERN = 5
    # dataIn.rd = 1, wait for dataIn.vld
    
DELAY = 6 #  time in accumulator [ms]
    # temp_delay_en = 1
    # wait for temp_delay_fin
    # temp_delay_en = 1
    
SEND_DATA = 7 # arg in acumulator
SEND_CONTROLL = 8
    # temp_dc = 0
    # temp_spi_data = accumulator, 
    # temp_spi_en = 1
    # wait for temp_spi_fin
    # temp_spi_en = 0
    


# Update Page states
# 1. Sends the SetPage Command
# 2. Sends the Page to be set to
# 3. Sets the start pixel to the left column
setPage = [
    LOAD, 
    0b00100010, 
    SEND_CONTROLL, # SetPage
    LOAD_PAGECNTR,
    SEND_CONTROLL, # PageNum
    LOAD,
    0,
    SEND_CONTROLL, # LeftColumn1
    LOAD,
    0b00010000,
    SEND_CONTROLL, # LeftColumn2
]

initSequenceA = [0xAE, # Set Display OFF
                0xD5, # SetClockDiv1
                0x80, # SetClockDiv2
                0xA8, # MultiPlex1
                0x1F, # MultiPlex2
                0x8D, # Access Charge Pump Setting
                0x14, # Enable Charge Pump
                0xD9, # Access Pre-charge Period Setting
                0xF1, # Set the Pre-charge Period 
                0xF1, # Set the Pre-charge Period (VCOMH1)
                0xF1, # Set the Pre-charge Period (VCOMH2)
                0x81, # Set Contrast Control for BANK0
               ]
                
initSequenceB = [0xA1, # InvertDisp1
                 0xC0, # InvertDisp2
                 0xDA, # ComConfig1
                 0x02, # ComConfig2
                ]


initOled = [
    OLED_ON,
    LOAD,
    10, 
    DELAY,
    * sendControlls(initSequenceA),
    LOAD, 0x0F, SEND_CONTROLL,# DispContrast2
    * sendControlls(initSequenceB)
    ]