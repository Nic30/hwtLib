from enum import Enum

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct


vlan_t = vecT(12)  
mac_t = vecT(6 * 8)


syncword = 0b1010101010101010101010101010101010101010101010101010101010101011
EthPreambule_t = HStruct(
    (vecT(7 * 8), "preambule"),
    (vecT(8), "startOfFrameDelimiter"),
    name="EthPreambule_t"
    )

Eth2Header_t = HStruct(
    (mac_t, "dst"),
    (mac_t, "src"),
    (vecT(2 * 8), "type"),
    name="Eth2Header_t"
    )


class ETHER_TYPE(Enum):
    IPv4 = 0x0800
    ARP = 0x0806
    # wake on LAN
    WoL = 0x0842
    IPX = 0x8137
    IPX_b = 0x8138
    QNX_qnet = 0x8204
    IPv6 = 0x86DD
    MPLS_unicast = 0x8847
    MPLS_multicast = 0x8848


def pprint_eth_addr(mac) :
    macStr = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (ord(mac[i]) for i in range(6))
    return macStr


def parse_eth_addr(macStr):
    splited = macStr.split(":")
    splited = map(lambda num: int(num, 16), splited)
    return b"".join(splited)
