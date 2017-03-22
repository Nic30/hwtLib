from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.typeShortcuts import vecT


ICMP_header = HStruct(
                    (vecT(8), "type"), (vecT(8), "code"), (vecT(16), "checksum"),
                    (vecT(32), "restOfHeader")  
                )

class ICMP_TYPE:
    ECHO_REPLY = 0
    DESTINATION_UNREACHABLE = 3 
    ECHO_REQUEST = 8
    ROUTER_ADVERTISEMENT = 9
    ROUTER_SOLICITATION = 10
    TIME_EXCEEDED = 11
    TRACEROUTE = 30
