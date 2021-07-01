from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.bits import Bits

"""
:note: Based on: Universal Serial Bus Communications Class Subclass Specification
    for Ethernet Emulation Model Devices, Revision 1.0, February 2, 2005
"""


class EEM_PACKET_TYPE:
    DATA_PAYLOAD = 0
    COMMAND = 1


eem_packet_header_data_t = HStruct(
    (BIT, "bmType"),
    (BIT, "bmCRC"),  # see :class:`~.EEM_bmCRC`
    (Bits(14), "ethFrameLen"),
)


class EEM_bmCRC:
    DEADBEEF = 0
    CALCULATED = 1


eem_packet_command_t = HStruct(
    (BIT, "bmType"),
    (BIT, "bmReserved"), # must be set to 0
    (Bits(3), "bmEEMCmd"),  # see :class:`~.EEM_bmEEMCmd`
    (Bits(11), "bmEEMCmdParam"),
)


class EEM_bmEEMCmd:
    ECHO = 0 # :note: used for usb link validation
    ECHO_RESPONSE = 1
    SUSPEND_HINT = 2
    RESPONSE_HINT = 3
    RESPONSE_COMPLETE_HINT = 4
    TICKLE = 5
