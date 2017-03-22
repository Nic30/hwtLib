from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct

vlan_t = vecT(12)  
mac_t = vecT(6 * 8)


syncword = 0b1010101010101010101010101010101010101010101010101010101010101011
ethPreambule = HStruct(
    (vecT(7 * 8), "preambule"),
    (vecT(8), "startOfFrameDelimiter")
    )

eth2Header = HStruct(
    (mac_t, "dst"),
    (mac_t, "src"),
    (vecT(2 * 8), "type")
    )



