from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.bits import Bits
from hwtLib.types.ctypes import uint16_t


# LSB:MSB
class TCP_FLAGS():
    FIN = 0
    SYN = 1
    RST = 2
    PSH = 3  # push
    ACK = 4
    URG = 5
    ECN = 6  # ECN Echo
    CWR = 7  # reduced


tcp_header_t = HStruct(
    (Bits(4), "headerLen"),  # number of 32bit words in TCP header (min=5)
    (Bits(4), "reserved"),
    (Bits(8), "flags"),
    (uint16_t, "window"),
    (uint16_t, "checksum"),
    (uint16_t, "urgentPtr"),
)
