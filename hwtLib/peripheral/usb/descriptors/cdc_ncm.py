from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint32_t, uint16_t
from hwt.hdl.types.stream import HStream

# Table 3-1: Sixteen Bit NCM Transfer Header (NTH16)
NTH16_SIGNATURE = 0x484D434E
nth16_t = HStruct(
    (uint32_t, "dwSignature"),
    (uint16_t, "wHeaderLength"),
    (uint16_t, "wSequence"),
    (uint16_t, "wBlockLength"),
    (uint16_t, "wNdpIndex"),
)

# Table 3-3: Sixteen-bit NCM Datagram Pointer Table (NDP16)
NDP16_SIGNATURE_WITH_CRC = 0x304D434E
NDP16_SIGNATURE_WITHOUT_CRC = 0x314D434E
ndp16_wDatagram_t = HStruct(
    (uint16_t, "index"),
    (uint16_t, "length"),
)
ndp16_head_t = HStruct(
    (uint32_t, "dwSignature"),
    (uint16_t, "wLength"),
    (uint16_t, "reserved0"),
)
ndp16_t = HStruct(
    *ndp16_head_t.fields,
    (HStream(ndp16_wDatagram_t), "wDatagram"), # last must be 0,0 and works as sentinel
)
