from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct


ICMP_header_t = HStruct(
    (Bits(8), "type"), (Bits(8), "code"), (Bits(16), "checksum"),
    (Bits(32), "restOfHeader"),
    name="ICMP_header_t"
)

ICMP_echo_header_t = HStruct(
    (Bits(8), "type"), (Bits(8), "code"), (Bits(16), "checksum"),
    (Bits(16), "identifier"), (Bits(16), "seqNo"),
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
