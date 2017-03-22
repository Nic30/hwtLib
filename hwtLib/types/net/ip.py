from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.typeShortcuts import vecT
from hwtLib.types.ctypes import uint8_t, uint16_t

IPv4 = 4
IPv6 = 6

ICMP = 1
IGMP = 2
TCP = 6
UDP = 17
ENCAP = 41
OSPF = 89
SCTP = 132

l4port_t = vecT(16)
ipv4_t = vecT(4 * 8)
ipv6_t = vecT(128)
ipver_t = vecT(4)

IPv4Header = HStruct(
    (vecT(4), "version"), (vecT(4), "ihl"), (vecT(6), "dscp"), (vecT(2), "ecn"), (uint16_t, "payloadLen"),
    (vecT(16), "id"), (vecT(3), "flags"), (vecT(13), "fragmentOffset"),
    (uint8_t, "ttl"), (uint8_t, "protocol"), (vecT(16), "headerChecksum"),
    (ipv4_t, "src"),
    (ipv4_t, "dst"),
    name="IPv4Header"
    )


IPv6Header = HStruct(
    (vecT(4), "version"), (vecT(8), "trafficClass"), (vecT(20), "flowLabel"),
    (uint16_t, "payloadLen"), (vecT(8), "nextHeader"), (vecT(8), "hopLimit"),
    (ipv6_t, "src"),
    (ipv6_t, "dst"),
    name="IPv6Header"
    )