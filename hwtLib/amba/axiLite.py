from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.std import VectSignal
from hwt.serializer.ip_packager.interfaces.intfConfig import IntfConfig
from hwt.simulator.agentBase import AgentBase
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_intf_common import AxiMap, Axi_hs
from hwtLib.amba.sim.agentCommon import BaseAxiAgent


#################################################################
class AxiLite_addr(Axi_hs):
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        
    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        Axi_hs._declr(self)
        
    def _getSimAgent(self):
        return AxiLite_addrAgent

class AxiLite_addrAgent(BaseAxiAgent):
    def doRead(self, s):
        return s.read(self.intf.addr)
    
    def doWrite(self, s, data):
        s.write(data, self.intf.addr)

#################################################################
class AxiLite_r(Axi_hs):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        
    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.resp = VectSignal(2)
        Axi_hs._declr(self)
        
    def _getSimAgent(self):
        return AxiLite_rAgent

class AxiLite_rAgent(BaseAxiAgent):
    def doRead(self, s):
        r = s.read
        intf = self.intf
        
        return (r(intf.data), r(intf.resp))


    def doWrite(self, s, data):
        intf = self.intf
        w = s.w
        if data is None:
            data = [None for _ in range(2)]
        
        data, resp = data
        
        w(data, intf.data)
        w(resp, intf.resp)

#################################################################    
class AxiLite_w(Axi_hs):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        
    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.strb = VectSignal(self.DATA_WIDTH // 8)
        Axi_hs._declr(self)
        
    def _getSimAgent(self):
        return AxiLite_wAgent

class AxiLite_wAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.r
        return (r(intf.data), r(intf.strb))
    
    def doWrite(self, s, data):
        intf = self.intf
        w = s.w
        if data is None:
            data = [None for _ in range(2)]
        
        data, strb = data
        
        w(data, intf.data)
        w(strb, intf.strb)

#################################################################    
class AxiLite_b(Axi_hs):
    def _declr(self):
        self.resp = VectSignal(2)
        Axi_hs._declr(self)

    def _getSimAgent(self):
        return AxiLite_bAgent

class AxiLite_bAgent(BaseAxiAgent):
    def doRead(self, s):
        return s.r(self.intf.resp)
    
    def doWrite(self, s, data):
        s.w(data, self.intf.resp)


#################################################################
class AxiLite(Interface):
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        
    def _declr(self):
        with self._paramsShared():
            self.aw = AxiLite_addr()
            self.ar = AxiLite_addr()
            self.w = AxiLite_w()
            self.r = AxiLite_r(masterDir=DIRECTION.IN)
            self.b = AxiLite_b(masterDir=DIRECTION.IN)
            
    def _getIpCoreIntfClass(self):
        return IP_AXILite
    
    def _getSimAgent(self):
        return AxiLiteAgent


class AxiLiteAgent(AgentBase):
    """
    Composite agent with agent for every axi channel
    enable is shared
    """
    @property
    def enable(self):
        return self.__enable
    
    @enable.setter
    def enable(self, v):
        self.__enable = v
        
        for o in [self.ar, self.aw, self.r, self.w, self.b]:
            o.enable = v

    def __init__(self, intf):
        self.__enable = True
        self.intf = intf
        
        ag = lambda i: i._getSimAgent()(i) 
        
        self.ar = ag(intf.ar)
        self.aw = ag(intf.aw)
        self.r = ag(intf.r)
        self.w = ag(intf.w)
        self.b = ag(intf.b)
                
        
        
    def getDrivers(self):
        return (self.aw.getDrivers() + 
                self.ar.getDrivers() + 
                self.w.getDrivers() + 
                self.r.getMonitors() + 
                self.b.getMonitors()
                )
    
    
    def getMonitors(self):
        return (self.aw.getMonitors() + 
                self.ar.getMonitors() + 
                self.w.getMonitors() + 
                self.r.getDrivers() + 
                self.b.getDrivers()
                )

#################################################################
class AxiLite_addr_xil(AxiLite_addr):
    _NAME_SEPARATOR = ''
class AxiLite_r_xil(AxiLite_r):
    _NAME_SEPARATOR = ''
class AxiLite_w_xil(AxiLite_w):
    _NAME_SEPARATOR = ''
class AxiLite_b_xil(AxiLite_b):
    _NAME_SEPARATOR = ''
    
class AxiLite_xil(AxiLite):
    def _declr(self):
        with self._paramsShared():
            self.aw = AxiLite_addr_xil()
            self.ar = AxiLite_addr_xil()
            self.w = AxiLite_w_xil()
            self.r = AxiLite_r_xil(masterDir=DIRECTION.IN)
            self.b = AxiLite_b_xil(masterDir=DIRECTION.IN)
    
class IP_AXILite(IntfConfig):
    def __init__(self):
        super().__init__()
        self.name = "aximm"
        self.version = "1.0"
        self.vendor = "xilinx.com" 
        self.library = "interface"
        a_sigs = ['addr', 'valid', 'ready']
        self.map = {'aw': AxiMap('aw', a_sigs),
                    'w' : AxiMap('w', ['data', 'strb', 'valid', 'ready']),
                    'ar' : AxiMap('ar', a_sigs),
                     'r' : AxiMap('r', ['data', 'resp', 'valid', 'ready']),
                     'b' : AxiMap('b', ['valid', 'ready', 'resp'])
                     }

        
    def postProcess(self, component, entity, allInterfaces, thisIf):
        self.endianness = "little"
        self.addWidthParam(thisIf, "ADDR_WIDTH", thisIf.ADDR_WIDTH)
        self.addWidthParam(thisIf, "DATA_WIDTH", thisIf.DATA_WIDTH)
        self.addSimpleParam(thisIf, "PROTOCOL", "AXI4LITE")
        self.addSimpleParam(thisIf, "READ_WRITE_MODE", "READ_WRITE")