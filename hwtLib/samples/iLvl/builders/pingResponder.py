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
    """
    Listen for echo request on rx axi stream interface and respond with echo response on tx interface
    
    :note: incoming checksum is not checked
    :attention: you have to ping "ping -s 0 <ip>" because unit ignores additional data in packet and linux by
        defaults adds it
    """

    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.IS_BIGENDIAN = Param(True)

    def _declr(self):
        addClkRstn(self)

        self.myIp = Signal(dtype=ipv4_t)

        with self._paramsShared():
            self.rx = AxiStream()
            self.tx = AxiStream()

    def req_load(self, parsed, regs, freeze):
        """
        Load request from parser input into registers
        
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
            reg = getattr(regs, name)

            if isinstance(In, StructIntf):
                self.req_load(In, reg, freeze)
            else:
                if isinstance(reg, Value) or not isinstance(reg, RtlMemoryBase):
                    # we have an exact value to use, ignore this intput
                    In.rd ** 1
                    continue

                If(In.vld & ~freeze,
                   reg ** In.data
                )
                In.rd ** ~freeze

    def connect_resp(self, resp, forgeIn, sendingReply):
        """
        Connect response data on inputs of frame forge
        
        :param resp: registers with response data
        :param forgeIn: input interface of frame forge
        :param sendingRepply: flag which signalizes that data should be forged into frame and send
        """

        t = resp._dtype

        if isinstance(t, Bits):
            forgeIn.data ** resp
            forgeIn.vld ** sendingReply
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
        sendingReply = self._reg("sendingReply", defVal=0)
        resp = self._reg("resp", echoFrame_t)
        isEchoReq = self._reg("isEchoReq", defVal=0)

        resp.icmp.type = resp.icmp.type._dtype.fromPy(ICMP_TYPE.ECHO_REPLY)
        resp.icmp.code = resp.icmp.code._dtype.fromPy(0)
        resp.icmp.checksum = self.icmp_checksum(resp.icmp)
        
        
        parsed = AxiSBuilder(self, self.rx).parse(echoFrame_t)
        self.req_load(parsed, resp, sendingReply)

        t = parsed.icmp.type
        If(t.vld,
           isEchoReq ** t.data._eq(ICMP_TYPE.ECHO_REQUEST)
        )

        def setup_frame_forge(out):
            out.DATA_WIDTH.set(self.DATA_WIDTH)
            out.IS_BIGENDIAN.set(self.IS_BIGENDIAN)

        txBuilder, forgeIn = AxiSBuilder.forge(self,
                                               echoFrame_t,
                                               AxiStream,
                                               setup_frame_forge)

        self.connect_resp(resp, forgeIn, sendingReply)
        tx = txBuilder.end
        self.tx ** tx
        
        
        If(self.rx.last & self.rx.valid,
           sendingReply ** (self.myIp._eq(resp.ip.dst) & isEchoReq) 
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

