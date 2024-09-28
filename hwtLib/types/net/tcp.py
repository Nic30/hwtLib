from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint16_t, uint32_t, uint8_t
from hwtLib.types.net.ip import l4port_t, ipv4_t, ipv6_t

TCP_flags_t = HStruct(
    (BIT, "cwr"),  # Congestion Window Reduced
    (BIT, "ece"),  # ECN-Echo
    (BIT, "urg"),  # Urgent pointer field is significant.
    (BIT, "ack"),  # This bit indicates that the device sending the segment is conveying an acknowledgment for a message it has received (such as a SYN).
    (BIT, "psh"),  # Push function (send data immediately)
    (BIT, "rst"),  # Reset the connection.
    # * Receipt of any TCP segment from any device with which the device receiving the segment
    #  does not currently have a connection (other than a SYN requesting a new connection.)
    # * Receipt of a message with an invalid or incorrect Sequence Number or
    #   Acknowledgment Number field, indicating the message may belong to
    #   a prior connection or is spurious in some other way.
    # * Receipt of a SYN message on a port where there is no process listening for connections.
    #
    (BIT, "syn"),  # This bit indicates that the segment is being used to initialize a connection.
                  # SYN stands for synchronize, in reference to the sequence number synchronization.
    (BIT, "fin"),  # a connection termination request to the other device, while also possibly carrying data like a regular segment
)

#  https://www.ietf.org/rfc/rfc9293.html
#   0                   1                   2                   3
#   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
#  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#  |          Source Port          |       Destination Port        |
#  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#  |                        Sequence Number                        |
#  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#  |                    Acknowledgment Number                      |
#  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#  |  Data |       |C|E|U|A|P|R|S|F|                               |
#  | Offset| Rsrvd |W|C|R|C|S|S|Y|I|            Window             |
#  |       |       |R|E|G|K|H|T|N|N|                               |
#  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#  |           Checksum            |         Urgent Pointer        |
#  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#  |                           [Options]                           |
#  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#  |                                                               :
#  :                             Data                              :
#  :                                                               |
#  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

TCP_seq_t = uint32_t
TCP_header_t = HStruct(
    (l4port_t, "srcp"), (l4port_t, "dstp"),
    (TCP_seq_t, "seq"),
    (TCP_seq_t, "ack_seq"),
    (HBits(4), "doff"),  #  The number of 32-bit words in the TCP header. (including options)
    (HBits(4), "reserved1"),  # sent as zero
    (uint8_t, "flags"),
    (uint16_t, "window"),  # Indicates the number of octets of data the sender of this segment is willing to accept from the receiver at one time.
    (HBits(16), "checksum"),
    (uint16_t, "z"), # used to implement interrupt like behavior, forcing some data with higher priority
#  Options are multiple of 8 bits in length (padded with 0 if smaller). All options are included in the checksum.
    name="TCP_header_t"
)

# TCP option - End of Option List (0)
TCP_OPT_EOL = 0
TCP_OPT_EOL_LEN = 1

# TCP option - No Operation (1)
TCP_OPT_NOP = 1
TCP_OPT_NOP_LEN = 1

# TCP option - Maximum Segment Size (2)
#  Conveys the size of the largest segment the sender of the segment wishes
# to receive. Used only in connection request (SYN) messages.
TCP_OPT_MSS = 2
TCP_OPT_MSS_LEN = 4

# TCP option - Window Scale (3)
# Allows devices to specify larger window sizes than would be possible
# with the normal Window field. (window <<= WSCALE)
TCP_OPT_WSCALE = 3
TCP_OPT_WSCALE_LEN = 3

# TCP option - Sack Permit (4) (Selective Acknowledgment Permitted.)
TCP_OPT_SACKPERM = 4
TCP_OPT_SACKPERM_LEN = 2

# TCP option - Selective Acknowledgment
# length is variable
# Allows devices supporting the optional selective acknowledgment feature
# to specify non-contiguous blocks of data that have been received so they
# are not retransmitted if intervening segments do not show up and need to be retransmitted.
TCP_OPT_SELACK = 5

# TCP option - Timestamp
TCP_OPT_TIMESTAMP = 8
TCP_OPT_TIMESTAMP_LEN = 10

# :note: pseudo headers are used for checksum calculation
TCP_IPv4PseudoHeader_t = HStruct(
    (ipv4_t, "src"),
    (ipv4_t, "dst"),
    (HBits(8), "zeros"), (uint8_t, "protocol"), (uint16_t, "tcpLength"),
    name = "TCP_IPv4PseudoHeader_t"
)

TCP_IPv6PseudoHeader_t = HStruct(
    (ipv6_t, "src"),
    (ipv6_t, "dst"),
    (uint32_t, "tcpLength"),
    (HBits(24), "zeros"), (HBits(8), "nextHeader"),
    name = "TCP_IPv6PseudoHeader_t"
)
