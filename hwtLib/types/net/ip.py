from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint8_t, uint16_t


IPv4 = 4
IPv6 = 6

IHL_DEFAULT = 5

l4port_t = Bits(16)
ipv4_t = Bits(4 * 8)
ipv6_t = Bits(128)
ipver_t = Bits(4)


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
    (Bits(4), "version"), (Bits(4), "ihl"), (Bits(6), "dscp"), (Bits(2), "ecn"), (uint16_t, "totalLen"),
    (Bits(16), "id"), (Bits(3), "flags"), (Bits(13), "fragmentOffset"),
    (uint8_t, "ttl"), (uint8_t, "protocol"), (Bits(16), "headerChecksum"),
    (ipv4_t, "src"),
    (ipv4_t, "dst"),
    name="IPv4Header_t"
    )


IPv6Header_t = HStruct(
    (Bits(4), "version"), (Bits(8), "trafficClass"), (Bits(20), "flowLabel"),
    (uint16_t, "payloadLen"), (Bits(8), "nextHeader"), (Bits(8), "hopLimit"),
    (ipv6_t, "src"),
    (ipv6_t, "dst"),
    name="IPv6Header_t"
    )
