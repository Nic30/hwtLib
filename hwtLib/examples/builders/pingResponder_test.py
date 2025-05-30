#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

from hwt.hdl.types.utils import HConst_from_words
from hwt.math import sizeof
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import Bits3valToInt
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.amba.axi4s import Axi4StreamFrameUtils
from hwtLib.examples.builders.pingResponder import Axi4SPingResponder, \
    echoFrame_t
from hwtLib.types.net.ethernet import eth_addr_parse, ETHER_TYPE
from hwtLib.types.net.icmp import ICMP_TYPE, ICMP_echo_header_t
from hwtLib.types.net.ip import IPv4, IHL_DEFAULT, IPv4Header_t, IP_PROTOCOL
from hwtSimApi.constants import CLK_PERIOD


def add_16b(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)


def checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = msg[i] + (msg[i + 1] << 8)
        s = add_16b(s, w)

    return ~s & 0xffff


def hstruct_checksum(structVal):
    """
    Checksum of values in StructValue instance
    """
    valAsBytes = iterBits(structVal, bitsInOne=8)
    valAsBytes = [x.val for x in valAsBytes]
    return checksum(valAsBytes)


def pingResponder_model(packetStructVal):
    """
    Modify ICMP Echo Request to an ICMP Echo Reply packet.

    :param packet: struct val of packet
    """
    packet = iterBits(packetStructVal, bitsInOne=8, skipPadding=False)
    packet = [Bits3valToInt(p) for p in packet]
    eth = 0
    # swap eht addr
    (packet[(eth + 0):(eth + 6)],
     packet[(eth + 6):(eth + 12)]) = (packet[(eth + 6):(eth + 12)],
                                      packet[(eth + 0):(eth + 6)])

    ip = 2 * 6 + 2
    # Swap source and destination address.
    (packet[(ip + 12):(ip + 16)],
     packet[(ip + 16):(ip + 20)]) = (packet[(ip + 16):(ip + 20)],
                                     packet[(ip + 12):(ip + 16)])

    icmp = ip + 20
    # Change ICMP type code to Echo Reply (0).
    packet[icmp] = ICMP_TYPE.ECHO_REPLY

    # clean checksum
    packet[icmp + 2] = 0
    packet[icmp + 3] = 0

    # Calculate new  ICMP Checksum field.
    checksum = 0
    # for every 16-bit of the ICMP payload:
    for i in range(icmp, len(packet), 2):
        half_word = (packet[i] << 8) + (packet[i + 1])
        checksum += half_word
    # Get one's complement of the checksum.
    checksum = ~checksum & 0xffff
    # Put the new checksum back into the packet. (bigendian)
    packet[icmp + 2] = checksum >> 8
    packet[icmp + 3] = checksum & ((1 << 8) - 1)

    return bytes(packet)


class Axi4SPingResponderTC(SimTestCase):
    DATA_WIDTH = 32

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = Axi4SPingResponder()
        dut.DATA_WIDTH = cls.DATA_WIDTH
        cls.compileSim(dut)

    def create_ICMP_echo_frame(self,
                               ethSrc="00:1:2:3:4:5", ethDst="6:7:8:9:10:11",
                               ipSrc="192.168.0.1", ipDst="192.168.0.2"):

        v = echoFrame_t.from_py({
                "eth": {
                    "src": eth_addr_parse(ethSrc),
                    "dst": eth_addr_parse(ethDst),
                    "type": ETHER_TYPE.IPv4,
                },
                "ip": {
                    "version": IPv4,
                    "ihl": IHL_DEFAULT,
                    "dscp": 0,
                    "ecn": 0,
                    "totalLen": sizeof(IPv4Header_t) + sizeof(ICMP_echo_header_t),
                    "id": 0,
                    "flags": 0,
                    "fragmentOffset": 0,
                    "ttl": 100,
                    "protocol": IP_PROTOCOL.ICMP,
                    "headerChecksum": 0,
                    "src": socket.inet_aton(ipSrc),
                    "dst": socket.inet_aton(ipDst)
                },
                "icmp": {
                    "type": ICMP_TYPE.ECHO_REQUEST,
                    "code": 0,
                    "checksum": 0,
                    "identifier": 0,
                    "seqNo": 0,
                }
            })

        v.ip.headerChecksum.val = hstruct_checksum(v.ip)
        v.icmp.checksum.val = hstruct_checksum(v.icmp)

        return v

    def test_struct_packUnpack(self):
        f = self.create_ICMP_echo_frame()
        asBytes = iterBits(f, bitsInOne=8, skipPadding=False)
        asBytes = [Bits3valToInt(x) for x in asBytes]

        f_out = HConst_from_words(echoFrame_t, asBytes, dataWidth=8)

        self.assertEqual(f, f_out)

        _f = f
        f = f_out
        asBytes = iterBits(f, bitsInOne=8, skipPadding=False)
        asBytes = [Bits3valToInt(x) for x in asBytes]

        f_out = HConst_from_words(echoFrame_t, asBytes, dataWidth=8)

        self.assertEqual(_f, f_out)

    def test_reply1x(self):
        dut = self.dut
        f = self.create_ICMP_echo_frame()
        
        fu = Axi4StreamFrameUtils(self.DATA_WIDTH)
        dut.rx._ag.data.extend(fu.pack_frame(f))
        dut.myIp._ag.data.append(
            int.from_bytes(socket.inet_aton("192.168.0.2"), byteorder="little")
        )
        self.runSim(50 * CLK_PERIOD)

        res = fu.unpack_frame(echoFrame_t, dut.tx._ag.data)
        model_res = pingResponder_model(f)

        _res = iterBits(res, bitsInOne=8, skipPadding=False)
        _res = bytes(map(Bits3valToInt, _res))
        # print("")
        # print("f", f)
        # print("res", res)
        # print("model_res", HConst_from_words(echoFrame_t, model_res, dataWidth=8))

        self.assertEqual(_res, model_res)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4SPingResponderTC("test_reply1x")])
    suite = testLoader.loadTestsFromTestCase(Axi4SPingResponderTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
