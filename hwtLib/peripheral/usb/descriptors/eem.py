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
    ("bmType", BIT),
    ("bmCRC", BIT),  # see :class:`~.EEM_bmCRC`
    ("ethFrameLen", Bits(14)),
)


class EEM_bmCRC:
    DEADBEEF = 0
    CALCULATED = 1


eem_packet_command_t = HStruct(
    ("bmType", BIT),
    ("bmReserved", BIT), # must be set to 0
    ("bmEEMCmd", Bits(3)),  # see :class:`~.EEM_bmEEMCmd`
    ("bmEEMCmdParam", Bits(11)),
)


class EEM_bmEEMCmd:
    ECHO = 0 # :note: used for usb link validation
    ECHO_RESPONSE = 1
    SUSPEND_HINT = 2
    RESPONSE_HINT = 3
    RESPONSE_COMPLETE_HINT = 4
    TICKLE = 5
