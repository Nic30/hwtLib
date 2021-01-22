from typing import List

from hwt.hdl.constants import DIRECTION, INTF_DIRECTION
from hwt.interfaces.std import VectSignal
from hwt.serializer.ip_packager import IpPackager
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_intf_common import AxiMap, Axi_hs
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from ipCorePackager.component import Component
from ipCorePackager.intfIpMeta import IntfIpMeta
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator


#################################################################
class Axi3Lite_addr(Axi_hs):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.ADDR_WIDTH = Param(32)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        Axi_hs._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi3Lite_addrAgent(sim, self)


class Axi3Lite_addrAgent(BaseAxiAgent):
    """
    :ivar ~.data: iterable of addr
    """

    def get_data(self):
        return self.intf.addr.read()

    def set_data(self, data):
        self.intf.addr.write(data)

    def create_addr_req(self, addr, prot=None):
        assert prot is None, "Axi3Lite_addr does not have a prot signal"
        return addr


#################################################################
class Axi3Lite_r(Axi_hs):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.resp = VectSignal(2)
        Axi_hs._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AxiLite_rAgent(sim, self)


class AxiLite_rAgent(BaseAxiAgent):
    """
    :ivar ~.data: iterable of tuples (data, resp)
    """

    def get_data(self):
        intf = self.intf

        return (intf.data.read(), intf.resp.read())

    def set_data(self, data):
        intf = self.intf
        if data is None:
            data = [None for _ in range(2)]

        data, resp = data

        intf.data.write(data)
        intf.resp.write(resp)


#################################################################
class Axi3Lite_w(Axi_hs):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.strb = VectSignal(self.DATA_WIDTH // 8)
        Axi_hs._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi3Lite_wAgent(sim, self)


class Axi3Lite_wAgent(BaseAxiAgent):
    """
    :ivar ~.data: iterable of tuples (data, strb)
    """

    def get_data(self):
        intf = self.intf
        return (intf.data.read(), intf.strb.read())

    def set_data(self, data):
        intf = self.intf
        if data is None:
            intf.data.write(None)
            intf.strb.write(None)
        else:
            data, strb = data
            intf.data.write(data)
            intf.strb.write(strb)


#################################################################
class Axi3Lite_b(Axi_hs):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.resp = VectSignal(2)
        Axi_hs._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi3Lite_bAgent(sim, self)


class Axi3Lite_bAgent(BaseAxiAgent):
    """
    :ivar ~.data: iterable of resp
    """

    def get_data(self):
        return self.intf.resp.read()

    def set_data(self, data):
        self.intf.resp.write(data)


#################################################################
class Axi3Lite(Interface):
    """
    AMBA AXI3-lite interface

    https://static.docs.arm.com/ihi0022/d/IHI0022D_amba_axi_protocol_spec.pdf

    .. hwt-autodoc::
    """
    AW_CLS = Axi3Lite_addr
    AR_CLS = Axi3Lite_addr
    W_CLS = Axi3Lite_w
    R_CLS = Axi3Lite_r
    B_CLS = Axi3Lite_b
    LEN_WIDTH = 0

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.HAS_R = True
        self.HAS_W = True

    def _declr(self):
        with self._paramsShared():
            if self.HAS_R:
                self.ar = self.AR_CLS()
                self.r = self.R_CLS(masterDir=DIRECTION.IN)

            if self.HAS_W:
                self.aw = self.AW_CLS()
                self.w = self.W_CLS()
                self.b = self.B_CLS(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_Axi3Lite

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi3LiteAgent(sim, self)

    def _getWordAddrStep(self):
        """
        :return: size of one word in unit of address
        """
        return int(self.DATA_WIDTH) // self._getAddrStep()

    def _getAddrStep(self):
        """
        :return: how many bits is one unit of address (e.g. 8 bits for  char * pointer,
             36 for 36 bit bram)
        """
        return 8


class Axi3LiteAgent(AgentBase):
    """
    Composite simulation agent with agent for every axi channel
    change of enable is propagated to each child

    data for each agent is stored in agent for given channel (ar, aw, r, ... property)
    """

    def __init__(self, sim: HdlSimulator, intf):
        self.__enable = True
        self.intf = intf

        def ag(intf):
            intf._initSimAgent(sim)
            agent = intf._ag
            return agent

        if intf.HAS_R:
            self.ar = ag(intf.ar)
            self.r = ag(intf.r)

        if intf.HAS_W:
            self.aw = ag(intf.aw)
            self.w = ag(intf.w)
            self.b = ag(intf.b)

    def getEnable(self):
        return self.__enable

    def setEnable(self, en):
        if self.__enable != en:
            self.__enable = en
            if self.intf.HAS_R:
                self.ar.setEnable(en)
                self.r.setEnable(en)
            if self.intf.HAS_W:
                self.aw.setEnable(en)
                self.w.setEnable(en)
                self.b.setEnable(en)

    def getDrivers(self):
        drvs = []
        if self.intf.HAS_W:
            drvs.extend(
                self.aw.getDrivers()
                +self.w.getDrivers()
                +self.b.getMonitors()
            )

        if self.intf.HAS_R:
            drvs.extend(
                self.ar.getDrivers()
                +self.r.getMonitors()
            )
        return drvs

    def getMonitors(self):
        mons = []
        if self.intf.HAS_W:
            mons.extend(
                self.aw.getMonitors()
                +self.w.getMonitors()
                +self.b.getDrivers()
            )
        if self.intf.HAS_R:
            mons.extend(
                self.ar.getMonitors()
                +self.r.getDrivers()
            )
        return mons

    def create_addr_req(self, *args, **kwargs):
        if self.intf.HAS_R:
            ch = self.ar
        else:
            ch = self.aw
        return ch.create_addr_req(*args, **kwargs)


#################################################################
class IP_Axi3Lite(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "aximm"
        # quartus 17.10 does not have axi3lite
        self.quartus_name = "axi4lite"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        a_sigs = ['addr', 'valid', 'ready']
        self.map = {
            'aw': AxiMap('aw', a_sigs),
            'w': AxiMap('w', ['data', 'strb', 'valid', 'ready']),
            'ar': AxiMap('ar', a_sigs),
            'r': AxiMap('r', ['data', 'resp', 'valid', 'ready']),
            'b': AxiMap('b', ['valid', 'ready', 'resp'])
        }

    def get_quartus_map(self):
        if self.quartus_map is None:
            self.quartus_map = self._toLowerCase(self.map)
        return IntfIpMeta.get_quartus_map(self)

    def _toLowerCase(self, d):
        if isinstance(d, dict):
            new_d = {}
            for k, v in d.items():
                new_d[k.lower()] = self._toLowerCase(v)
            return new_d
        else:
            return d.lower()

    def asQuartusTcl(self, buff: List[str], version: str, component: Component,
                     packager: IpPackager, thisIf: Interface):
        IntfIpMeta.asQuartusTcl(self, buff, version,
                                component, packager, thisIf)
        name = getSignalName(thisIf)
        if thisIf._direction == INTF_DIRECTION.MASTER:
            self.quartus_prop(buff, name, "readIssuingCapability", 1)
            self.quartus_prop(buff, name, "writeIssuingCapability", 1)
            self.quartus_prop(buff, name, "combinedIssuingCapability", 1)
        else:
            self.quartus_prop(buff, name, "readAcceptanceCapability", 1)
            self.quartus_prop(buff, name, "writeAcceptanceCapability", 1)
            self.quartus_prop(buff, name, "combinedAcceptanceCapability", 1)
            self.quartus_prop(buff, name, "readDataReorderingDepth", 1)
            self.quartus_prop(buff, name, "bridgesToMaster", "")

    def postProcess(self, component: Component,
                    packager: IpPackager,
                    thisIf: Axi3Lite):
        self.endianness = "little"
        thisIntfName = packager.getInterfaceLogicalName(thisIf)
        self.addWidthParam(thisIntfName, "ADDR_WIDTH",
                           thisIf.ADDR_WIDTH, packager)
        self.addWidthParam(thisIntfName, "DATA_WIDTH",
                           thisIf.DATA_WIDTH, packager)
        self.addSimpleParam(thisIntfName, "PROTOCOL", "AXI4LITE")
        self.addSimpleParam(thisIntfName, "READ_WRITE_MODE", "READ_WRITE")
