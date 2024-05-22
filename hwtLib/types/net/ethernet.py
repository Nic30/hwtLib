from typing import Union, List

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct

vlan_t = HBits(12)
eth_mac_t = HBits(6 * 8)

eth_syncword = 0b1010101010101010101010101010101010101010101010101010101010101011

EthPreamble_t = HStruct(
    (HBits(7 * 8), "preambule"),
    (HBits(8), "startOfFrameDelimiter"),
    name="EthPreamble_t"
)

Eth2Header_t = HStruct(
    (eth_mac_t, "dst"),
    (eth_mac_t, "src"),
    (HBits(2 * 8), "type"), # :see: :class:`~.ETHER_TYPE`
    name="Eth2Header_t"
)

Tag802_1q = HStruct(
    (HBits(16), "tpid"),
    (HBits(16), "tci")
)

Eth802_1qHeader_t = HStruct(
    (eth_mac_t, "dst"),
    (eth_mac_t, "src"),
    (Tag802_1q, "tag"),
    (HBits(2 * 8), "type"),
    name="Eth802_1qHeader_t"
)


class ETHER_TYPE():
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
    VLAN_1Q = 0x8100
    VLAN_1AD = 0x88A8


def eth_addr_format(mac: List[Union[int, str]]):
    assert len(mac) == 6
    macStr = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % tuple(
        ord(x) if isinstance(x, str) else int(x)
        for x in mac)
    return macStr


def eth_addr_parse(macStr:str):
    splited = macStr.split(":")
    splited = map(lambda num: int(num, 16).to_bytes(1, byteorder='big'), splited)
    return b"".join(splited)
