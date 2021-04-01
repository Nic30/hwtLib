from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.defs import BIT

"""
:attention: on USB the LSB bits are sent first
"""


class USB_VER:
    USB1_0 = "1.0"
    USB1_1 = "1.1"
    USB2_0 = "2.0"


class PID:
    """
    USB Protocol layer packet identifier values
    (Specifies the type of transaction)

    :attention: visualy written in msb-first, transmited in lsb first

    :note: packet formats are described in structs in this file
    """
    # Address for host-to-device transfer
    TOKEN_OUT = 0b0001
    # Address for device-to-host transfer
    TOKEN_IN = 0b1001
    # Start of frame marker (sent each ms)
    TOKEN_SOF = 0b0101
    # Address for host-to-device control transfer
    TOKEN_SETUP = 0b1101

    # Even-numbered data packet
    DATA_0 = 0b0011
    # Odd-numbered data packet
    DATA_1 = 0b1011
    # Data packet for high-bandwidth isochronous transfer (USB 2.0)
    DATA_2 = 0b0111
    # Data packet for high-bandwidth isochronous transfer (USB 2.0)
    DATA_M = 0b1111

    # Data packet accepted
    HS_ACK = 0b0010
    # Data packet not accepted; please retransmit
    HS_NACK = 0b1010
    # Transfer impossible; do error recovery
    HS_STALL = 0b1110
    # Data not ready yet (USB 2.0)
    HS_NYET = 0b0110

    # Low-bandwidth USB preamble
    PREAMBLE = 0b1100
    # Split transaction error (USB 2.0)
    ERR = 0b1100
    # High-bandwidth (USB 2.0) split transaction
    SPLIT = 0b1000
    # Check if endpoint can accept data (USB 2.0)
    PING = 0b0100


addr_t = Bits(7)
endp_t = Bits(4)
crc5_t = Bits(5)
crc16_t = Bits(16)
pid_t = Bits(4)

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
    (pid_t, "pid"),
    (addr_t, "addr"),
    (endp_t, "endp"),
    (crc5_t, "crc5"),  # :note: not involves PID, only addr, endp
)

USB_MAX_FRAME_LEN = {
    USB_VER.USB1_0: 8,
    USB_VER.USB1_1: 1023,
    USB_VER.USB2_0: 1024,
}


def get_packet_data_t(usb_ver: USB_VER):
    max_frame_len = USB_MAX_FRAME_LEN[usb_ver]
    # pid has to be one of DATA_0, DATA_1, DATA_2, DATA_M
    return HStruct(
        (pid_t, "pid"),
        (HStream(Bits(8), frame_len=(1, max_frame_len)), "data")
        ,
        (crc16_t, "crc"),  # :note: not involves PID, only data
    )

"""
There are three type of handshake packets which consist simply of the PID

* ACK - Acknowledgment that the packet has been successfully received.
* NAK - Reports that the device temporary cannot send or received data.
  Also used during interrupt transactions to inform the host there is no data to send.
* STALL - The device finds its in a state that it requires intervention from the host.
"""
packet_hs_t = HStruct(
    (pid_t, "pid"),
)

"""
The SOF (Start of Frame) packet consisting of an 11-bit frame number is sent by the host
every 1ms ± 500ns on a full speed bus or every 125 µs ± 0.0625 µs on a high speed bus.
"""
frame_number_t = Bits(11)
packet_sof_t = HStruct(
    (pid_t, "pid"),
    (frame_number_t, "frame_number"),
    (crc5_t, "crc5"),  # :note: not involves PID, only frame_number
)

request_type_t = HStruct(
    (Bits(5), "recipient"),
    (Bits(2), "type"),
    (Bits(1), "data_transfer_direction"),
)


class REQUEST_TYPE_DIRECTION:
    """
    Values for request_type_t.recipient
    """
    HOST_TO_DEV = 0
    DEV_TO_HOST = 1


class REQUEST_TYPE_TYPE:
    """
    Values for request_type_t.type
    """
    STANDARD = 0
    CLASS = 1
    VENDOR = 2


class REQUEST_TYPE_RECIPIENT:
    """
    Values for request_type_t.data_transfer_direction
    """
    DEVICE = 0
    INTERFACE = 1
    ENDPOINT = 2
    OTHER = 3


# used as a data for setup transactions
device_request_t = HStruct(
    (request_type_t, "bmRequestType"),
    (Bits(1 * 8), "bRequest"),
    # Word-sized field that varies according to request
    (Bits(2 * 8), "wValue"),
    # Word-sized field that varies according to
    # request; typically used to pass an index or offset
    (Bits(2 * 8), "wIndex"),
    # Number of bytes to transfer if there is a Data stage
    (Bits(2 * 8), "wLength"),
)


class REQUEST:
    """
    Values for device_request_t.bRequest
    """
    GET_STATUS = 0x00  # dev, intf, ep
    CLEAR_FEATURE = 0x01  # dev, intf, ep
    SET_FEATURE = 0x03  # dev, intf, ep
    SET_ADDRESS = 0x05  # dev
    GET_DESCRIPTOR = 0x06  # dev
    SET_DESCRIPTOR = 0x07  # dev
    GET_CONFIGURATION = 0x08  # dev
    SET_CONFIGURATION = 0x09  # dev
    SYNCH_FRAME = 0x12  # ep
    GET_INTERFACE = 0x0A  # intf
    SET_INTERFACE = 0x11  # intf
