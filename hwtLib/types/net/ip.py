from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct
from hwtLib.types.ctypes import uint8_t, uint16_t


IPv4 = 4
IPv6 = 6

IHL_DEFAULT = 5

l4port_t = vecT(16)
ipv4_t = vecT(4 * 8)
ipv6_t = vecT(128)
ipver_t = vecT(4)


class IP_FLAGS():
    DONT_FRAGMENT = 0b010
    MORE_FRAGMENTS = 0b100


class IP_PROTOCOL():
    HOPOPT = 0
    ICMP = 1
    IGMP = 2
    GGP = 3
    IPv4 = 4  # (encapsulated)
    TCP = 6
    EGP = 8
    IGP = 9
    UDP = 17
    ENCAP = 41
    IPv6_route = 43
    IPv6_frag = 44
    IPv6_ICMP = 58
    IPv6_noNxt = 59
    IPv6_opts = 60
    OSPF = 89
    IPIP = 94
    ETHERIP = 97
    QNX = 106
    L2TP = 115
    SMP = 121
    SCTP = 132


IPv4Header_t = HStruct(
    (vecT(4), "version"), (vecT(4), "ihl"), (vecT(6), "dscp"), (vecT(2), "ecn"), (uint16_t, "totalLen"),
    (vecT(16), "id"), (vecT(3), "flags"), (vecT(13), "fragmentOffset"),
    (uint8_t, "ttl"), (uint8_t, "protocol"), (vecT(16), "headerChecksum"),
    (ipv4_t, "src"),
    (ipv4_t, "dst"),
    name="IPv4Header_t"
    )


IPv6Header_t = HStruct(
    (vecT(4), "version"), (vecT(8), "trafficClass"), (vecT(20), "flowLabel"),
    (uint16_t, "payloadLen"), (vecT(8), "nextHeader"), (vecT(8), "hopLimit"),
    (ipv6_t, "src"),
    (ipv6_t, "dst"),
    name="IPv6Header_t"
    )
