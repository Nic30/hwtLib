#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.hdl.value import Value
from hwt.interfaces.std import Signal
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.mainBases import RtlMemoryBase
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.types.net.eth import Eth2Header_t
from hwtLib.types.net.icmp import ICMP_echo_header_t, ICMP_TYPE
from hwtLib.types.net.ip import IPv4Header_t, ipv4_t
from hwt.serializer.verilog.serializer import VerilogSerializer


echoFrame_t = HStruct(
        (Eth2Header_t, "eth"),
        (IPv4Header_t, "ip"),
        (ICMP_echo_header_t, "icmp"),
    )


# https://github.com/hamsternz/FPGA_Webserver/tree/master/hdl/icmp
class PingResponder(Unit):
    """
    Listen for echo request on rx axi stream interface and respond
    with echo response on tx interface

    :note: incoming checksum is not checked
    :attention: you have to ping "ping -s 0 <ip>" because unit ignores
        additional data in packet and linux by defaults adds it

    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.IS_BIGENDIAN = Param(True)
        self.USE_STRB = Param(True)

    def _declr(self):
        addClkRstn(self)

        self.myIp = Signal(dtype=ipv4_t)

        with self._paramsShared(exclude=({"USE_STRB"}, set())):
            self.rx = AxiStream()

        with self._paramsShared():
            self.tx = AxiStream()._m()

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

            if isinstance(In, StructIntf):
                self.req_load(In, reg, freeze)
            else:
                if isinstance(reg, Value) or not isinstance(reg, RtlMemoryBase):
                    # we have an exact value to use, ignore this intput
                    In.rd(1)
                    continue

                If(In.vld & ~freeze,
                   reg(In.data)
                )
                In.rd(~freeze)

    def connect_resp(self, resp, forgeIn, sendingReply):
        """
        Connect response data on inputs of frame forge

        :param resp: registers with response data
        :param forgeIn: input interface of frame forge
        :param sendingRepply: flag which signalizes that data
            should be forged into frame and send
        """

        t = resp._dtype

        if isinstance(t, Bits):
            forgeIn.data(resp)
            forgeIn.vld(sendingReply)
        else:
            for f in t.fields:
                name = f.name
                In = getattr(resp, name)

                # switch dst and src
                if name == "src":
                    name = "dst"
                elif name == "dst":
                    name = "src"

                Out = getattr(forgeIn, name)
                self.connect_resp(In, Out, sendingReply)

    def icmp_checksum(self, header):
        """
        :note: we do not need to care about endianity because parser/forge will swap it for us
            and we can work with little endians only
        :return: checksum for icmp header
        """

        # type, code, checksum = 0
        return ~(header.identifier +
                 header.seqNo
                 )

    def _impl(self):
        # tmp registers
        sendingReply = self._reg("sendingReply", def_val=0)
        resp = self._reg("resp", echoFrame_t)
        isEchoReq = self._reg("isEchoReq", def_val=0)

        # set fields of reply
        resp.icmp.type = resp.icmp.type._dtype.from_py(ICMP_TYPE.ECHO_REPLY)
        resp.icmp.code = resp.icmp.code._dtype.from_py(0)
        resp.icmp.checksum = self.icmp_checksum(resp.icmp)

        # parse input frame
        parsed = AxiSBuilder(self, self.rx).parse(echoFrame_t)
        self.req_load(parsed, resp, sendingReply)

        t = parsed.icmp.type
        If(t.vld,
           isEchoReq(t.data._eq(ICMP_TYPE.ECHO_REQUEST))
        )

        def setup_frame_forge(out):
            out.DATA_WIDTH = self.DATA_WIDTH
            out.IS_BIGENDIAN = self.IS_BIGENDIAN

        # create output frame
        txBuilder, forgeIn = AxiSBuilder.forge(self,
                                               echoFrame_t,
                                               AxiStream,
                                               setup_frame_forge)

        self.connect_resp(resp, forgeIn, sendingReply)
        tx = txBuilder.end
        self.tx(tx)

        # update state flags
        If(self.rx.last & self.rx.valid,
           sendingReply(self.myIp._eq(resp.ip.dst) & isEchoReq)
        ).Elif(tx.valid & tx.last,
           sendingReply(0)
        )


if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it only when this script is running as main
    from hwt.synthesizer.utils import toRtl
    # we create instance of our unit
    u = PingResponder()
    # there is more of synthesis methods. toRtl() returns formated hdl string
    print(toRtl(u))

