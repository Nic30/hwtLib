from hwt.hdl.typeShortcuts import vec
from hwt.math import log2ceil


class ETH:
    PREAMBLE_1B = vec(0x55, 8)
    PREAMBLE = vec(0x55555555555555, 7*8)  # (7* 0x55)
    SFD = vec(0xD5, 8)  # frame delimiter


class ETH_BITRATE:
    M_10M = 0
    M_100M = 1
    M_1G = 2
    M_2_5G = 3
    M_10G = 4
    M_25G = 5
    M_100G = 6
    M_200G = 7
    M_400G = 8
    M_1T = 9

    def get_siganl_width(self, max_mode: int):
        return log2ceil(max_mode)
