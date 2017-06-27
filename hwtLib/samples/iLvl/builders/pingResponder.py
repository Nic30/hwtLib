from hwt.code import If
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.value import Value
from hwt.interfaces.std import Signal
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.mainBases import RtlMemoryBase
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.types.net.eth import Eth2Header_t
from hwtLib.types.net.icmp import ICMP_echo_header_t, ICMP_TYPE
from hwtLib.types.net.ip import IPv4Header_t, ipv4_t


echoFrame_t = HStruct(
        (Eth2Header_t, "eth"),
        (IPv4Header_t, "ip"),
        (ICMP_echo_header_t, "icmp"),
    )


# https://github.com/hamsternz/FPGA_Webserver/tree/master/hdl/icmp
class PingResponder(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)

        self.myIp = Signal(dtype=ipv4_t)

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
                if isinstance(reg, Value) or not isinstance(reg, RtlMemoryBase):
                    # we have an exact value to use, ignore this intput
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
        # Concat(vec(0, 8), header.code) = 0
        return ~(header.identifier + 
                 header.seqNo + 
                 header.payload[16:] + 
                 header.payload[32:16])

    def _impl(self):
        parsed = AxiSBuilder(self, self.rx).parse(echoFrame_t)
        # sof = AxiSBuilder(self, self.rx).startOfFrame()

        sendingReply = self._reg("sendingReply", defVal=0)
        resp = self._reg("resp", echoFrame_t)
        isEchoReq = self._reg("isEchoReq", defVal=0)

        resp.icmp.type = resp.icmp.type._dtype.fromPy(ICMP_TYPE.ECHO_REPLY)
        resp.icmp.code = resp.icmp.code._dtype.fromPy(0)
        
        
        resp.icmp.checksum = self.icmpChecksum(resp.icmp)
        self.reqLoad(parsed, resp, sendingReply)

        t = parsed.icmp.type
        If(t.vld,
           isEchoReq ** t.data._eq(ICMP_TYPE.ECHO_REQUEST)
        )

        def setup_output(out):
            out.DATA_WIDTH.set(self.DATA_WIDTH)

        txBuilder, forgeIn = AxiSBuilder.forge(self,
                                             echoFrame_t,
                                             AxiStream,
                                             setup_output)

        self.connectResp(resp, forgeIn, sendingReply)
        tx = txBuilder.end
        self.tx ** tx
        
        
        If(self.rx.last & self.rx.valid,
           # note that src and dst were swapped
           sendingReply ** (self.myIp._eq(resp.ip.src) & isEchoReq) 
        ).Elif(tx.valid & tx.last,
           sendingReply ** 0
        )


if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it only when this script is running as main
    from hwt.synthesizer.shortcuts import toRtl
    # we create instance of our unit
    u = PingResponder()
    # there is more of synthesis methods. toRtl() returns formated hdl string
    print(toRtl(u))
