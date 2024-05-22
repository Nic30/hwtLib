from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint16_t, uint32_t, uint8_t
from hwtLib.types.net.ip import l4port_t

TCP_flags_t = HStruct(
    (BIT, "cwr"),
    (BIT, "ece"),
    (BIT, "urg"),
    (BIT, "ack"),
    (BIT, "psh"),
    (BIT, "rst"),
    (BIT, "syn"),
    (BIT, "fin"),
)

TCP_header_t = HStruct(
    (l4port_t, "srcp"), (l4port_t, "dstp"),
    (uint32_t, "seq"),
    (uint32_t, "ack_seq"),
    (HBits(4), "doff"),
    (HBits(4), "reserved1"),
    (uint8_t, "flags"),
    (uint16_t, "window"), (HBits(16), "checksum"),
    (uint16_t, "urg_ptr"),
    name="TCP_header_t"
)

