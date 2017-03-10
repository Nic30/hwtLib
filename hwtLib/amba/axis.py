from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.std import Signal, VectSignal
from hwt.serializer.ip_packager.interfaces.intfConfig import IntfConfig
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtLib.amba.axi_intf_common import Axi_user, Axi_id, Axi_strb


# http://www.xilinx.com/support/documentation/ip_documentation/ug761_axi_reference_guide.pdf
class AxiStream_withoutSTRB(Interface):
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.last = Signal()
        self.ready = Signal(masterDir=DIRECTION.IN)
        self.valid = Signal()

    def _getIpCoreIntfClass(self):
        return IP_AXIStream


class AxiStream(AxiStream_withoutSTRB, Axi_strb):
    def _config(self):
        AxiStream_withoutSTRB._config(self)
        Axi_strb._config(self)

    def _declr(self):
        AxiStream_withoutSTRB._declr(self)
        Axi_strb._declr(self)

    def _getSimAgent(self):
        return AxiStreamAgent


class AxiStream_withUserAndNoStrb(AxiStream_withoutSTRB, Axi_user):
    def _config(self):
        AxiStream_withoutSTRB._config(self)
        Axi_user._config(self)

    def _declr(self):
        AxiStream_withoutSTRB._declr(self)
        Axi_user._declr(self)


class AxiStream_withId(Axi_id, AxiStream):
    def _config(self):
        Axi_id._config(self)
        AxiStream._config(self)

    def _declr(self):
        Axi_id._declr(self)
        AxiStream._declr(self)

    def _getSimAgent(self):
        return AxiStream_withIdAgent


class AxiStream_withUserAndStrb(AxiStream, Axi_user):
    def _config(self):
        AxiStream._config(self)
        Axi_user._config(self)

    def _declr(self):
        AxiStream._declr(self)
        Axi_user._declr(self)

    def _getSimAgent(self):
        return AxiStream_withUserAndStrbAgent


class AxiStreamAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        data = r(intf.data)
        strb = r(intf.strb)
        last = r(intf.last)

        return (data, strb, last)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.w

        if data is None:
            data = [None for _ in range(3)]

        _data, strb, last = data

        w(_data, intf.data)
        w(strb, intf.strb)
        w(last, intf.last)


class AxiStream_withIdAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        _id = r(intf.id)
        data = r(intf.data)
        strb = r(intf.strb)
        last = r(intf.last)

        return (_id, data, strb, last)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.w

        if data is None:
            data = [None for _ in range(4)]

        _id, data, strb, last = data

        w(_id, intf.id)
        w(data, intf.data)
        w(strb, intf.strb)
        w(last, intf.last)


class AxiStream_withUserAndStrbAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        data = r(intf.data)
        strb = r(intf.strb)
        user = r(intf.user)
        last = r(intf.last)

        return (data, strb, user, last)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.w

        if data is None:
            data = [None for _ in range(4)]

        data, strb, user, last = data

        w(data, intf.data)
        w(strb, intf.strb)
        w(user, intf.user)
        w(last, intf.last)


class IP_AXIStream(IntfConfig):
    def __init__(self):
        super().__init__()
        self.name = "axis"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {'id': "TID",
                    'data': "TDATA",
                    'last': "TLAST",
                    'valid': "TVALID",
                    'strb': "TSTRB",
                    'keep': "TKEEP",
                    'user': 'TUSER',
                    'ready': "TREADY"
                    }
