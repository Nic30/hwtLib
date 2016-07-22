from hwtLib.proc.ssd1306cntrl.instructions import *

def sendControlls(controllData):
    code = []
    for c in controllData:
        code.extend([LOAD_DATA, c, *send_controll()])
    return code

def instrSet(instr, pin, val):
    """
    bit  7   val
    bits 6-4 pin
    bits 3-0 instr
    """
    
    if val:
        v = 1
    else:
        v = 0
    
    v << 4
    assert pin < ((1 << 4) - 1)
    v |= pin 
    v << 3
    v |= instr
    return instr

def oledOn():
    return [
        instrSet(PIN_SET, PIN_DC, 0),
        instrSet(PIN_SET, PIN_VDD, 0) 
    ]

def oledInitFinalize():
    return  [
        instrSet(PIN_SET, PIN_VBAT, 0),
        LOAD_DATA, 100,
        DO_WAIT,
        instrSet(PIN_SET, PIN_RES, 0),
        LOAD_DATA, 100,
        DO_WAIT,
        instrSet(PIN_SET, PIN_RES, 1),
    ]

def selectRow():
    # Update Page states
    # 1. Sends the SetPage Command
    # 2. Sends the Page to be set to
    # 3. Sets the start pixel to the left column
    return [
        LOAD_DATA, 0x22, *send_controll(), # SetPage
        LOAD_ROW,        *send_controll(), # PageNum
        LOAD_DATA, 0,    *send_controll(), # LeftColumn1
        LOAD_DATA, 0x10, *send_controll(), # LeftColumn2
    ]


# data is expected to be in accumulator
def send_char():
    code = [STORE_CHAR]
    for _ in range(8):
        code.append(LOAD_BM_ROW)
        code.extend(send_data())
    code.append(COLUMN_INCR)
    
    return code
    
    
# LOAD_BM_ROW has to be executed first
# arg in acumulator (char_index is column, page_tmp is row)
def send_data():
    return [
        instrSet(PIN_SET, PIN_DC, 1),
        SEND    
    ]

# data is expected to be in accumulator
def send_controll():    
    return [
        instrSet(PIN_SET, PIN_DC, 0),
        SEND    
    ]
    


initSequenceA = [
    0xAE, # Set Display OFF
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
                
initSequenceB = [
    0xA1, # InvertDisp1
    0xC0, # InvertDisp2
    0xDA, # ComConfig1
    0x02, # ComConfig2
]

initOled = [
    *oledOn(),
    LOAD_DATA, 100, DO_WAIT,
    * sendControlls(initSequenceA),
    LOAD_DATA, 0x0F, *send_controll(), # DispContrast2
    * sendControlls(initSequenceB),
    * oledInitFinalize(),
    LOAD_DATA, 0xAF, *send_controll(), # Dispaly ON
]


def sendText(text):
    code = []
    code.append(ROW_CLR)
    code.append(COLUMN_CLR)
    code.extend(selectRow())
    
    for ch in text:
        code.extend((LOAD_DATA, ord(ch)))
        code.extend(send_char())
        if ch == '\n':
            code.extend((COLUMN_CLR, ROW_INCR))
    return code
 
        
    
simpleCodeExample = initOled + sendText("ABC")


if __name__ == "__main__":
    from  pprint import pprint
    pprint(simpleCodeExample)

