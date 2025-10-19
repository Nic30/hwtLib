from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint8_t, uint16_t

IPv4 = 4
IPv6 = 6

IHL_DEFAULT = 5

l4port_t = HBits(16)
ipv4_t = HBits(4 * 8)
ipv6_t = HBits(128)
ipver_t = HBits(4)


class IP_FLAGS():
    DONT_FRAGMENT = 0b010
    MORE_FRAGMENTS = 0b100

# [todo] consider using python stdlib _socket.IPPROTO_AH and alike
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
    (HBits(4), "ihl"), (HBits(4), "version"), (HBits(2), "ecn"), (HBits(6), "dscp"), (uint16_t, "totalLen"),
    (HBits(16), "id"), (HBits(13), "fragmentOffset"), (HBits(3), "flags"),
    (uint8_t, "ttl"), (uint8_t, "protocol"), (HBits(16), "headerChecksum"),
    (ipv4_t, "src"),
    (ipv4_t, "dst"),
    name="IPv4Header_t"
)

IPv6Header_t = HStruct(
    (HBits(4), "version"), (HBits(8), "trafficClass"), (HBits(20), "flowLabel"),
    (uint16_t, "payloadLen"), (HBits(8), "nextHeader"), (HBits(8), "hopLimit"),
    (ipv6_t, "src"),
    (ipv6_t, "dst"),
    name="IPv6Header_t"
)
IPv6ExtCommonHeader_t = HStruct(
    (HBits(8), "nextHeader"), (HBits(8), "headerExtensionLen"), (HBits(16+32), "data"), # length of extension header + its data is (headerExtensionLen + 1) * 8 bytes
    name="IPv6ExtCommonHeader_t"
)


# checksum calculation https://gist.github.com/david-hoze/0c7021434796997a4ca42d7731a7073a

