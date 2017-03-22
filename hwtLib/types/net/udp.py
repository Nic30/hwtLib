from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.typeShortcuts import vecT
from hwtLib.types.ctypes import uint16_t, uint8_t, uint32_t
from hwtLib.types.net.eth import l4port_t
from hwtLib.types.net.ip import ipv4_t, ipv6_t


UDP_header = HStruct(
    (l4port_t, "srcp"), (l4port_t, "dstp"),
    (uint16_t, "length"), (vecT(16), "checksum"),
    name="UDP_header"
    )

UDP_IPv4PseudoHeader = HStruct(
                        (ipv4_t, "src"),
                        (ipv4_t, "dst"),
                        (vecT(8), "zeros"), (uint8_t, "protocol"), (uint16_t, "udpLength")
                        ) + UDP_header
UDP_IPv4PseudoHeader.name = "UDP_IPv4PseudoHeader" 

UDP_IPv6PseudoHeader = HStruct(
                        (ipv6_t, "src"),
                        (ipv6_t, "dst"),
                        (uint32_t, "udpLength")
                        (vecT(24), "zeros"), (vecT(8), "nextHeader")
                        ) + UDP_header
UDP_IPv6PseudoHeader.name = "UDP_IPv6PseudoHeader" 
