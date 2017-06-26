from hwt.code import If, Concat
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.value import Value
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.types.ctypes import uint32_t, uint8_t
from hwtLib.types.net.eth import Eth2Header
from hwtLib.types.net.icmp import ICMP_echo_header, ICMP_TYPE
from hwtLib.types.net.ip import IPv4Header
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hdlObjects.typeShortcuts import vec


echoFrame_t = HStruct(
        (Eth2Header, "eth"),
        (IPv4Header, "ip"),
        (ICMP_echo_header, "icmp"),
        (uint32_t, "payload")
    )


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


# https://github.com/hamsternz/FPGA_Webserver/tree/master/hdl/icmp
class PingResponder(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.rx = AxiStream()
            self.tx = AxiStream()

    def reqLoad(self, parsed, regs, freeze):
        """
        :param parsed: input interface with parsed fields of ICPM frame
        :param regs: registers for ICMP frame
        :param freeze: signal to freeze value in registers
        :param defVal: dictionary item from regs: default value
        :attention: dst and src are swapped
        """
        dtype = regs._dtype

        for f in dtype.fields:
            name = f.name
            In = getattr(parsed, name)

            # switch dst and src
            if name == "src":
                name = "dst"
            elif name == "dst":
                name = "src"
            reg = getattr(regs, name)

            if isinstance(In, StructIntf):
                self.reqLoad(In, reg, freeze)
            else:
                if isinstance(reg, (Value, RtlSignal)):
                    In.rd ** 1
                    continue

                If(In.vld & ~freeze,
                   reg ** In.data
                )
                In.rd ** ~freeze

    def connectResp(self, resp, forgeIn, sendingReply):
        t = resp._dtype

        if isinstance(t, Bits):
            forgeIn.data ** resp
            forgeIn.vld ** sendingReply
        else:
            for f in t.fields:
                name = f.name
                In = getattr(resp, name)
                Out = getattr(forgeIn, name)
                self.connectResp(In, Out, sendingReply)

    def icmpChecksum(self, header):
        return ~(Concat(vec(0, 8), header.code) +
                 header.identifier +
                 header.seqNo +
                 header.payload[16:] +
                 header.payload[32:16])

    def _impl(self):
        parsed = AxiSBuilder(self, self.rx).parse(echoFrame_t)
        # sof = AxiSBuilder(self, self.rx).startOfFrame()

        sendingReply = self._reg("sendingReply", defVal=0)
        resp = self._reg("resp", echoFrame_t)
        resp.icmp.type = uint8_t.fromPy(ICMP_TYPE.ECHO_REPLY)
        resp.icmp.code = uint8_t.fromPy(0)
        resp.icmp.checksum = self.icmpChecksum(resp.icmp)
        self.reqLoad(parsed, resp, sendingReply)

        def setup_output(out):
            out.DATA_WIDTH.set(self.DATA_WIDTH)

        builder, forgeIn = AxiSBuilder.forge(self,
                                             echoFrame_t,
                                             AxiStream,
                                             setup_output)

        self.connectResp(resp, forgeIn, sendingReply)

        self.tx ** builder.end

if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it only when this script is running as main
    from hwt.synthesizer.shortcuts import toRtl
    # we create instance of our unit
    u = PingResponder()
    # there is more of synthesis methods. toRtl() returns formated hdl string
    print(toRtl(u))

