from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.typeShortcuts import vecT

ICMP_header_t = HStruct(
                    (vecT(8), "type"), (vecT(8), "code"), (vecT(16), "checksum"),
                    (vecT(32), "restOfHeader"),
                    name="ICMP_header_t"
                )

ICMP_echo_header_t = HStruct(
                    (vecT(8), "type"), (vecT(8), "code"), (vecT(16), "checksum"),
                    (vecT(16), "identifier"), (vecT(16), "seqNo"),
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
