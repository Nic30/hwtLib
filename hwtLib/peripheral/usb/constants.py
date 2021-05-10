from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct

"""
:attention: on USB the LSB bits are sent first
"""


class USB_VER:
    """
    +-----------+-----------------------+
    | USB_VER   |  Speed                |
    +-----------+-----------------------+
    | 1.0 - 2.0 | Low Speed 1.5 Mbit/s  |
    +-----------+-----------------------+
    | 1.0 - 2.0 | Full Speed 12 Mbit/s  |
    +-----------+-----------------------+
    | 2.0       | High Speed 480 Mbit/s |
    +-----------+-----------------------+
    | 3.0       | SuperSpeed 5Gbit/s    |
    +-----------+-----------------------+
    | 3.1       | SuperSpeed+ 10Gbit/s  |
    +-----------+-----------------------+
    | 3.2       | SuperSpeed+ 20Gbit/s  |
    +-----------+-----------------------+
    | 4.0       | SuperSpeed+ 40Gbit/s  |
    +-----------+-----------------------+
    """
    USB1_0 = "1.0"
    USB1_1 = "1.1"
    USB2_0 = "2.0"
    USB3_0 = "3.0"
    USB3_1 = "3.1"
    USB3_2 = "3.2"
    USB4_0 = "4.0"

    @staticmethod
    def to_uint16_t(usbVer: str):
        assert len(usbVer) == 3, usbVer
        usb_ver_mayor, usb_ver_minor = usbVer.split(".")
        usb_ver_mayor = ord(usb_ver_mayor) - ord('0')
        usb_ver_minor = ord(usb_ver_minor) - ord('0')
        usb_ver_minor <<= 4
        return (usb_ver_minor | (usb_ver_mayor << 8))


class USB_PID:
    """
    USB Protocol layer packet identifier values
    (Specifies the type of transaction)

    :attention: visualy written in msb-first, transmited in lsb first

    :note: packet formats are described in structs in this file
    """

    @classmethod
    def is_token(cls, v: int):
        return v in (cls.TOKEN_OUT, cls.TOKEN_IN, cls.TOKEN_SOF, cls.TOKEN_SETUP)

    # Marks for host-to-device transfer
    TOKEN_OUT = 0b0001
    # Marks for device-to-host transfer
    TOKEN_IN = 0b1001
    # Marks start of frame marker (sent each ms)
    TOKEN_SOF = 0b0101
    # Marks for host-to-device control transfer
    TOKEN_SETUP = 0b1101
    # :note: setup transactions always uses DATA_0, but it may be fallowed by IN which starts with 0 and alternates between 0/1

    @classmethod
    def is_data(cls, v: int):
        return v in (cls.DATA_0, cls.DATA_1, cls.DATA_2, cls.DATA_M)

    # DATA_X is always relatd to a specific endpoint
    # Even-numbered data packet
    DATA_0 = 0b0011
    # Odd-numbered data packet
    DATA_1 = 0b1011
    # Data packet for high-bandwidth isochronous transfer (USB 2.0)
    DATA_2 = 0b0111
    # Data packet for high-bandwidth isochronous transfer (USB 2.0)
    DATA_M = 0b1111

    @classmethod
    def is_hs(cls, v: int):
        return v in (cls.HS_ACK, cls.HS_NACK, cls.HS_STALL, cls.HS_NYET)

    # Data packet accepted
    HS_ACK = 0b0010
    # Data packet not accepted; please retransmit
    HS_NACK = 0b1010
    # Transfer impossible; do error recovery
    HS_STALL = 0b1110
    # Data not ready yet (USB 2.0)
    HS_NYET = 0b0110

    # Low-bandwidth USB preamble (tells hubs to temporarily switch to low speed mode)
    PREAMBLE = 0b1100
    # Split transaction error (USB 2.0)
    ERR = 0b1100
    # High-bandwidth (USB 2.0) split transaction
    SPLIT = 0b1000
    # Check if endpoint can accept data (USB 2.0)
    PING = 0b0100


usb_addr_t = Bits(7)
usb_endp_t = Bits(4)
usb_crc5_t = Bits(5)
usb_crc16_t = Bits(16)
usb_pid_t = Bits(4)

"""
:attention: every packet starts with sync and ends in EOP,
    which is not in data structures below
"""

"""
There are three types of token packets,

* In - Informs the USB device that the host wishes to read information.
* Out - Informs the USB device that the host wishes to send information.
* Setup - Used to begin control transfers.
"""
packet_token_t = HStruct(
    (usb_pid_t, "pid"),
    (usb_addr_t, "addr"),
    (usb_endp_t, "endp"),
    (usb_crc5_t, "crc5"),  # :note: not involves USB_PID, only addr, endp
)

usb1_0_packet_data_t = HStruct(
    (usb_pid_t, "pid"),
    (HStream(Bits(8), frame_len=(1, 8)), "data"),
    (usb_crc16_t, "crc"),  # :note: not involves USB_PID, only data
)

usb1_1_packet_data_t = HStruct(
    (usb_pid_t, "pid"),
    (HStream(Bits(8), frame_len=(1, 1023)), "data"),
    (usb_crc16_t, "crc"),  # :note: not involves USB_PID, only data
)
usb2_0_packet_data_t = HStruct(
    (usb_pid_t, "pid"),
    (HStream(Bits(8), frame_len=(1, 1024)), "data"),
    (usb_crc16_t, "crc"),  # :note: not involves USB_PID, only data
)

"""
There are three type of handshake packets which consist simply of the USB_PID

* ACK - Acknowledgment that the packet has been successfully received.
* NAK - Reports that the device temporary cannot send or received data.
  Also used during interrupt transactions to inform the host there is no data to send.
* STALL - The device finds its in a state that it requires intervention from the host.
"""
packet_hs_t = HStruct(
    (usb_pid_t, "pid"),
)

"""
The SOF (Start of Frame) packet consisting of an 11-bit frame number is sent by the host
every 1ms ± 500ns on a full speed bus or every 125 µs ± 0.0625 µs on a high speed bus.
"""
frame_number_t = Bits(11)
packet_sof_t = HStruct(
    (usb_pid_t, "pid"),
    (frame_number_t, "frame_number"),
    (usb_crc5_t, "crc5"),  # :note: not involves USB_PID, only frame_number
)
