from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.typeShortcuts import vecT
from hwtLib.types.ctypes import uint16_t, uint8_t, uint32_t
from hwtLib.types.net.ip import ipv4_t, ipv6_t, l4port_t


UDP_header_t = HStruct(
    (l4port_t, "srcp"), (l4port_t, "dstp"),
    (uint16_t, "length"), (vecT(16), "checksum"),
    name="UDP_header_t"
    )

UDP_IPv4PseudoHeader_t = HStruct(
                        (ipv4_t, "src"),
                        (ipv4_t, "dst"),
                        (vecT(8), "zeros"), (uint8_t, "protocol"), (uint16_t, "udpLength")
                        ) + UDP_header_t
UDP_IPv4PseudoHeader_t.name = "UDP_IPv4PseudoHeader_t"

UDP_IPv6PseudoHeader_t = HStruct(
                        (ipv6_t, "src"),
                        (ipv6_t, "dst"),
                        (uint32_t, "udpLength"),
                        (vecT(24), "zeros"), (vecT(8), "nextHeader")
                        ) + UDP_header_t
UDP_IPv6PseudoHeader_t.name = "UDP_IPv6PseudoHeader_t"
