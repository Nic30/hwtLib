import socket
import unittest

from hwt.code import iterBits
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.iLvl.builders.pingResponder import PingResponder, \
    echoFrame_t
from hwtLib.types.net.eth import parse_eth_addr, ETHER_TYPE
from hwtLib.types.net.icmp import ICMP_TYPE, ICMP_echo_header_t
from hwtLib.types.net.ip import IPv4, IHL_DEFAULT, IPv4Header_t, IP_PROTOCOL


def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)


def checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = msg[i] + (msg[i + 1] << 8)
        s = carry_around_add(s, w)

    return ~s & 0xffff


def hstruct_checksum(structVal):
    """
    Checksum of values in StructValue instance
    """
    valAsShorts = iterBits(structVal, bitsInOne=8)
    valAsShorts = list(map(lambda x: x.val, valAsShorts))
    print(len(valAsShorts), structVal._dtype.sizeof())
    print(valAsShorts)
    return checksum(valAsShorts)


def pingResponder_model(packet):
    """
    :param packet: arrayy of bytes from packet
    """
    # Modify it to an ICMP Echo Reply packet.
    #
    # Note that I have not checked content of the packet, but treat all packets
    # been sent to our TUN device as an ICMP Echo Request.

    # Swap source and destination address.
    packet[12:16], packet[16:20] = packet[16:20], packet[12:16]

    # Change ICMP type code to Echo Reply (0).
    packet[20] = ICMP_TYPE.ECHO_REPLY

    # Calculate new  ICMP Checksum field.
    checksum = 0
    # for every 16-bit of the ICMP payload:
    for i in range(20, len(packet), 2):
        half_word = (packet[i] << 8) + (packet[i + 1])
        checksum += half_word
    # Get one's complement of the checksum.
    checksum = ~(checksum + 4) & 0xffff
    # Put the new checksum back into the packet.
    packet[22] = checksum >> 8
    packet[23] = checksum & ((1 << 8) - 1)

    return bytes(packet)


class PingResponderTC(SimTestCase):

    def create_ICMP_echo_frame(self, ethSrc="00:1:2:3:4:5", ethDst="6:7:8:9:10:11",
                                     ipSrc="192.168.0.1", ipDst="192.168.0.1"):

        v = echoFrame_t.fromPy({
                "eth" : {
                    "src": parse_eth_addr(ethSrc),
                    "dst": parse_eth_addr(ethDst),
                    "typ" : ETHER_TYPE.IPv4,
                },
                "ip" : {
                    "version": IPv4,
                    "ihl": IHL_DEFAULT,
                    "dscp": 0,
                    "ecn": 0,
                    "totalLen" : IPv4Header_t.sizeof() + ICMP_echo_header_t.sizeof(),
                    "id": 0,
                    "flags": 0,
                    "ttl": 100,
                    "protocol": IP_PROTOCOL.ICMP,
                    "checksum" : 0,
                    "src": socket.inet_aton(ipSrc),
                    "dst": socket.inet_aton(ipDst)
                },
                "icmp": {
                    "type": ICMP_TYPE.ECHO_REQUEST,
                    "code": 0,
                    "checksum": 0,
                    "identifier": 0,
                    "reqNo": 0
                },
                "payload": int.from_bytes(b"abcd", byteorder="big")        
            
            })

        v.ip.headerChecksum.val = hstruct_checksum(v.ip)
        v.icmp.checksum.val = hstruct_checksum(v.icmp)

        return v

    def test_reply1x(self):
        u = PingResponder()
        self.prepareUnit(u)

        f = self.create_ICMP_echo_frame()


if __name__ == "__main__":
    # this is how you can run testcase,
    # there are many way and lots of tools support direct running of tests (like eclipse)
    suite = unittest.TestSuite()

    # this is how you can select specific test
    # suite.addTest(SimpleTC('test_simple'))

    # this is how you add all test from testcase
    suite.addTest(unittest.makeSuite(PingResponderTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
