BURST_FIXED = 0b00
BURST_INCR = 0b01
BURST_WRAP = 0b10

def BYTES_IN_TRANS(n):
    assert isinstance(n, int)
    return n.bit_length() - 1


# http://www.gstitt.ece.ufl.edu/courses/fall15/eel4720_5721/labs/refs/AXI4_specification.pdf  p.65
CACHE_DEFAULT = 3 # Normal Non-cacheable Bufferable

PROT_DEFAULT = 0
QOS_DEFAULT = 0
LOCK_DEFAULT = 0
RESP_OKAY = 0
RESP_EXOKAY = 1
RESP_SLVERR = 2
RESP_DECERR = 3