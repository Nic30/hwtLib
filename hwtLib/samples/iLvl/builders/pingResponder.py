from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwt.synthesizer.param import Param
from hwt.interfaces.utils import addClkRstn
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwt.hdlObjects.types.struct import HStruct
from hwtLib.types.net.eth import Eth2Header
from hwtLib.types.net.ip import IPv4Header
from hwtLib.types.net.icmp import ICMP_header
from hwtLib.types.ctypes import uint32_t


echoFrame_t = HStruct(
        (Eth2Header, "eth"),
        (IPv4Header, "ip"),
        (ICMP_header, "icmp"),
        (uint32_t, "payload")
    )

# https://github.com/hamsternz/FPGA_Webserver/tree/master/hdl/icmp
class PingResponder(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        self.rx = AxiStream()
        self.tx = AxiStream()
    
    def _impl(self):
        parsed = AxiSBuilder(self, self.rx).parse(echoFrame_t)
        sof = AxiSBuilder(self, self.rx).startOfFrame()


if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it only when this script is running as main
    from hwt.synthesizer.shortcuts import toRtl
    # we create instance of our unit
    u = PingResponder()
    # there is more of synthesis methods. toRtl() returns formated hdl string
    print(toRtl(u))
