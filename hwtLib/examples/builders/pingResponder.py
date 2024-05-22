#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.const import HConst
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.hwIOs.std import HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.mainBases import RtlMemoryBase
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.types.net.ethernet import Eth2Header_t
from hwtLib.types.net.icmp import ICMP_echo_header_t, ICMP_TYPE
from hwtLib.types.net.ip import IPv4Header_t, ipv4_t


echoFrame_t = HStruct(
        (Eth2Header_t, "eth"),
        (IPv4Header_t, "ip"),
        (ICMP_echo_header_t, "icmp"),
    )


# https://github.com/hamsternz/FPGA_Webserver/tree/master/hdl/icmp
class Axi4SPingResponder(HwModule):
    """
    Listen for echo request on rx axi stream interface and respond
    with echo response on tx interface

    :note: incoming checksum is not checked
    :attention: you have to ping "ping -s 0 <ip>" because unit ignores
        additional data in packet and linux by defaults adds it

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(32)
        self.IS_BIGENDIAN = HwParam(True)
        self.USE_STRB = HwParam(True)

    @override
    def hwDeclr(self):
        addClkRstn(self)

        self.myIp = HwIOSignal(dtype=ipv4_t)

        with self._hwParamsShared(exclude=({"USE_STRB"}, set())):
            self.rx = Axi4Stream()

        with self._hwParamsShared():
            self.tx = Axi4Stream()._m()

    def req_load(self, parsed, regs, freeze):
        """
        Load request from parser input into registers

        :param parsed: input interface with parsed fields of ICPM frame
        :param regs: registers for ICMP frame
        :param freeze: signal to freeze value in registers
        :param def_val: dictionary item from regs: default value
        :attention: dst and src are swapped
        """
        dtype = regs._dtype

        for f in dtype.fields:
            name = f.name
            In = getattr(parsed, name)
            reg = getattr(regs, name)

            if isinstance(In, HwIOStruct):
                self.req_load(In, reg, freeze)
            elif isinstance(reg, HConst) or \
                    (isinstance(reg, HwIOSignal) and not isinstance(reg._sig, RtlMemoryBase)):
                # we have an exact value to use, ignore this intput
                In.rd(1)
                continue
            else:
                If(In.vld & ~freeze,
                   reg(In.data)
                )
                In.rd(~freeze)

    def connect_resp(self, resp, deparserIn, sendingReply):
        """
        Connect response data on inputs of frame deparser

        :param resp: registers with response data
        :param deparserIn: input interface of frame deparser
        :param sendingRepply: flag which signalizes that data
            should be deparsed into frame and send
        """

        t = resp._dtype

        if isinstance(t, HBits):
            deparserIn.data(resp)
            deparserIn.vld(sendingReply)
        else:
            for f in t.fields:
                name = f.name
                In = getattr(resp, name)

                # swap dst and src
                if name == "src":
                    name = "dst"
                elif name == "dst":
                    name = "src"

                Out = getattr(deparserIn, name)
                self.connect_resp(In, Out, sendingReply)

    def icmp_checksum(self, header):
        """
        :note: we do not need to care about endianity because parser/deparser
            will swap it for us and we can work with little endians only
        :return: checksum for icmp header
        """

        # type, code, checksum = 0
        return ~(header.identifier +
                 header.seqNo
                 )

    @override
    def hwImpl(self):
        # tmp registers
        sendingReply = self._reg("sendingReply", def_val=0)
        resp = self._reg("resp", echoFrame_t)
        isEchoReq = self._reg("isEchoReq", def_val=0)

        # set fields of reply
        resp.icmp.type._sig = resp.icmp.type._dtype.from_py(ICMP_TYPE.ECHO_REPLY)
        resp.icmp.code._sig = resp.icmp.code._dtype.from_py(0)
        resp.icmp.checksum._sig = self.icmp_checksum(resp.icmp)

        # parse input frame
        parsed = Axi4SBuilder(self, self.rx).parse(echoFrame_t)
        self.req_load(parsed, resp, sendingReply)

        t = parsed.icmp.type
        If(t.vld,
           isEchoReq(t.data._eq(ICMP_TYPE.ECHO_REQUEST))
        )

        def setup_frame_deparser(out):
            out.DATA_WIDTH = self.DATA_WIDTH
            out.IS_BIGENDIAN = self.IS_BIGENDIAN

        # create output frame
        txBuilder, deparserIn = Axi4SBuilder.deparse(self,
                                               echoFrame_t,
                                               Axi4Stream,
                                               setup_frame_deparser)

        self.connect_resp(resp, deparserIn, sendingReply)
        tx = txBuilder.end
        self.tx(tx)

        # update state flags
        If(self.rx.last & self.rx.valid,
           sendingReply(self.myIp._eq(resp.ip.dst) & isEchoReq)
        ).Elif(tx.valid & tx.last,
           sendingReply(0)
        )


if __name__ == "__main__":  # alias python main function
    from hwt.synth import to_rtl_str
    
    m = Axi4SPingResponder()
    print(to_rtl_str(m))

