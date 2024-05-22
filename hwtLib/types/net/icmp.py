from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct


ICMP_header_t = HStruct(
    (HBits(8), "type"), (HBits(8), "code"), (HBits(16), "checksum"),
    (HBits(32), "restOfHeader"),
    name="ICMP_header_t"
)

ICMP_echo_header_t = HStruct(
    (HBits(8), "type"), (HBits(8), "code"), (HBits(16), "checksum"),
    (HBits(16), "identifier"), (HBits(16), "seqNo"),
    name="ICMP_echo_header_t"
)


class ICMP_TYPE():
    ECHO_REPLY = 0
    DESTINATION_UNREACHABLE = 3
    REDIRECT = 5
    ECHO_REQUEST = 8
    ROUTER_ADVERTISEMENT = 9
    ROUTER_SOLICITATION = 10
    TIME_EXCEEDED = 11
    PARAMETER_PROBLE = 12
    TIMESTAMP = 13
    TIMESTAMP_REPLY = 14
    TRACEROUTE = 30
