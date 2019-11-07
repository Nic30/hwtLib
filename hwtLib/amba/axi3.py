from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import VectSignal, Signal
from hwt.synthesizer.param import Param
from hwtLib.amba.axi3Lite import Axi3Lite_addr, Axi3Lite, Axi3Lite_r, Axi3Lite_b,\
    IP_Axi3Lite
from hwtLib.amba.axi_intf_common import AxiMap, Axi_id, Axi_hs, Axi_strb
from hwtLib.amba.axis import AxiStream, AxiStreamAgent
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwt.serializer.ip_packager import IpPackager
from ipCorePackager.component import Component
from pycocotb.hdlSimulator import HdlSimulator


#####################################################################
class Axi3_addr(Axi3Lite_addr, Axi_id):
    """
    Axi3 address channel interface
    """
    LEN_WIDTH = 4
    LOCK_WIDTH = 2

    def _config(self):
        Axi3Lite_addr._config(self)
        Axi_id._config(self)
        self.USER_WIDTH = Param(0)

    def _declr(self):
        Axi3Lite_addr._declr(self)
        Axi_id._declr(self)
        self.burst = VectSignal(2)
        self.cache = VectSignal(4)
        self.len = VectSignal(self.LEN_WIDTH)
        self.lock = VectSignal(self.LOCK_WIDTH)
        self.prot = VectSignal(3)
        self.size = VectSignal(3)
        if self.USER_WIDTH:
            self.user = VectSignal(self.USER_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi3_addrAgent(sim, self)


class Axi3_addrAgent(AxiStreamAgent):
    """
    Simulation agent for :class:`.Axi3_addr` interface

    input/output data stored in list under "data" property
    data contains tuples (id, addr, burst, cache, len, lock,
    prot, size, qos, optionally user)
    """

    def __init__(self, sim: HdlSimulator, intf: Axi3_addr, allowNoReset=False):
        BaseAxiAgent.__init__(self, sim, intf, allowNoReset=allowNoReset)

        signals = [
            intf.id,
            intf.addr,
            intf.burst,
            intf.cache,
            intf.len,
            intf.lock,
            intf.prot,
            intf.size,
        ]
        if hasattr(intf, "user"):
            signals.append(intf.user)
        self._signals = tuple(signals)
        self._sigCnt = len(signals)


#####################################################################
class Axi3_w(Axi_hs, Axi_strb):
    """
    Axi3 write channel interface (simplified  AxiStream)
    """
    def _config(self):
        self.ID_WIDTH = Param(0)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = VectSignal(self.ID_WIDTH)
        self.data = VectSignal(self.DATA_WIDTH)
        Axi_strb._declr(self)
        self.last = Signal()
        Axi_hs._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        AxiStream._initSimAgent(self, sim)


#####################################################################
class Axi3_r(Axi3Lite_r, Axi_id):
    """
    Axi 3 read channel interface
    """
    def _config(self):
        Axi_id._config(self)
        Axi3Lite_r._config(self)

    def _declr(self):
        Axi_id._declr(self)
        Axi3Lite_r._declr(self)
        self.last = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi3_rAgent(sim, self)


class Axi3_rAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.Axi4_r` interface

    input/output data stored in list under "data" property
    data contains tuples (id, data, resp, last)
    """

    def get_data(self):
        intf = self.intf

        _id = intf.id.read()
        data = intf.data.read()
        resp = intf.resp.read()
        last = intf.last.read()

        return (_id, data, resp, last)

    def set_data(self, data):
        intf = self.intf

        if data is None:
            data = [None for _ in range(4)]

        _id, data, resp, last = data

        intf.id.write(_id)
        intf.data.write(data)
        intf.resp.write(resp)
        intf.last.write(last)


#####################################################################
class Axi3_b(Axi3Lite_b, Axi_id):
    """
    Axi3 write response channel interface
    """
    def _config(self):
        Axi_id._config(self)
        Axi3Lite_b._config(self)

    def _declr(self):
        Axi_id._declr(self)
        Axi3Lite_b._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi3_bAgent(sim, self)


class Axi3_bAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.Axi3_b` interface

    input/output data stored in list under "data" property
    data contains tuples (id, resp)
    """

    def get_data(self):
        intf = self.intf

        return intf.id.read(), intf.resp.read()

    def set_data(self, data):
        intf = self.intf

        if data is None:
            data = [None for _ in range(2)]

        _id, resp = data

        intf.id.write(_id)
        intf.resp.write(resp)


#####################################################################
class Axi3(Axi3Lite):
    """
    Axi3 bus interface
    """
    LOCK_WIDTH = 2
    LEN_WIDTH = 4

    def _config(self):
        Axi3Lite._config(self)
        self.ID_WIDTH = Param(6)
        self.ADDR_USER_WIDTH = Param(0)
        # self.DATA_USER_WIDTH = Param(0)

    def _declr(self):
        with self._paramsShared():
            self.aw = Axi3_addr()
            self.ar = Axi3_addr()
            for a in [self.aw, self.ar]:
                a.USER_WIDTH = self.ADDR_USER_WIDTH

            self.w = Axi3_w()
            self.r = Axi3_r(masterDir=DIRECTION.IN)
            self.b = Axi3_b(masterDir=DIRECTION.IN)
            # for d in [self.w, self.r, self.b]:
            #     d.USER_WIDTH = self.DATA_USER_WIDTH

    def _getIpCoreIntfClass(self):
        return IP_Axi3


class IP_Axi3(IP_Axi3Lite):
    """
    IP core interface meta for Axi3 interface
    """
    def __init__(self,):
        super(IP_Axi3, self).__init__()
        self.quartus_name = "axi"
        self.xilinx_protocol_name = "AXI3"
        A_SIGS = ['id', 'burst', 'cache', 'len', 'lock',
                  'prot', 'size', 'qos', 'user']
        AxiMap('ar', A_SIGS, self.map['ar'])
        AxiMap('r', ['id', 'last'], self.map['r'])
        AxiMap('aw', A_SIGS, self.map['aw'])
        AxiMap('w', ['id', 'last'], self.map['w'])
        AxiMap('b', ['id'], self.map['b'])

    def postProcess(self,
                    component: Component,
                    packager: IpPackager,
                    thisIf: Axi3):
        self.endianness = "little"
        thisIntfName = packager.getInterfaceLogicalName(thisIf)

        def param(name, val):
            return self.addSimpleParam(thisIntfName, name, str(val))

        # [TODO] width as expression instead of int
        param("ADDR_WIDTH", thisIf.aw.addr._dtype.bit_length())
        param("MAX_BURST_LENGTH", 256)
        param("NUM_READ_OUTSTANDING", 5)
        param("NUM_WRITE_OUTSTANDING", 5)
        param("PROTOCOL", self.xilinx_protocol_name)
        param("READ_WRITE_MODE", "READ_WRITE")
        param("SUPPORTS_NARROW_BURST", 0)

        A_U_W = int(thisIf.ADDR_USER_WIDTH)
        if A_U_W:
            param("AWUSER_WIDTH", A_U_W)
            param("ARUSER_WIDTH", A_U_W)
