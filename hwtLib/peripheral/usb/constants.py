from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct


class USB_VER:
    USB1_0 = "1.0"
    USB1_1 = "1.1"
    USB2_0 = "2.0"


class PID:
    """
    USB Protocol layer packet identifier values

    :attention: visualy writen in msb-first, transmited in lsb first
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
    (crc5_t, "crc5"),
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
        (HStream(Bits(8), frame_len=(1, max_frame_len)), "data"),
        (crc16_t, "crc"),
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
The SOF packet consisting of an 11-bit frame number is sent by the host
every 1ms ± 500ns on a full speed bus or every 125 µs ± 0.0625 µs on a high speed bus.
"""
frame_number_t = Bits(11)
packet_sof_t = HStruct(
    (pid_t, "pid"),
    (frame_number_t, "frame_number"),
    (crc5_t, "crc5"),
)
