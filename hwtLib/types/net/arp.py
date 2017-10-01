from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint16_t, uint8_t
from hwtLib.types.net.eth import mac_t
from hwtLib.types.net.ip import ipv4_t


class ARP_HW_TYPE():
    ETHERNET = 1
    FRAME_RELAY = 15
    FIBRE_CHANNEL = 18
    ARP_SEC = 32
    IP_SEC_TUNNEL = 31
    INIFNIBAND = 32


class ARP_OPTCODE():
    REQUEST = 1
    REPLY = 2
    REQUEST_REVERSE = 3

    class DRARP():
        REQUEST = 5
        REPLY = 6
        ERROR = 7

    IN_ARP_REQUEST = 8
    IN_ARP_REPLY = 9
    ARP_NAK = 10

    class MARS():
        REQUEST = 11
        MULTI = 12
        MSERV = 13
        JOIN = 14
        LEAVE = 15
        NAK = 16
        UNSERV = 17
        SJOIN = 18
        SLEAVE = 19
        GROUPLIST_REQUEST = 20
        GROUPLIST_REPLY = 21
        REDIRECT_MAP = 22

    MAPOS_UNARP = 23
    OP_EXP1 = 24
    OP_EXP2 = 25


arp_ipv4_t = HStruct(
        (uint16_t, "htype"),  # hardware type
        (uint16_t, "ptype"),  # protocol type
        (uint8_t, "hlen"),  # hardware address length
        (uint8_t, "plen"),  # protocol address length
        (uint16_t, "opcode"),
        (mac_t, "sHwAddr"),  # sender hw address
        (ipv4_t, "sProtAddr"),  # sender protocol address
        (mac_t, "tHwAddr"),  # target hw address
        (ipv4_t, "tProtAddr"),  # target protocol address
    )
