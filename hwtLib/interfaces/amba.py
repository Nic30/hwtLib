from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import s, D
from hdl_toolkit.synthesizer.interfaceLevel.interface import  Interface
from hdl_toolkit.synthesizer.param import Param
from hwtLib.interfaces.amba_agents import Axi4_addrAgent, Axi4_rAgent, \
    AxiStreamAgent, AxiStream_withUserAndStrbAgent, AxiLiteAgent, \
    AxiLite_addrAgent, AxiLite_rAgent, AxiLite_wAgent, AxiLite_bAgent,\
    AxiStream_withIdAgent
from hwtLib.interfaces.amba_ip import IP_AXIStream, IP_AXILite, IP_Axi4


# http://www.xilinx.com/support/documentation/ip_documentation/ug761_axi_reference_guide.pdf
class AxiStream_withoutSTRB(Interface):
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.data = s(dtype=vecT(self.DATA_WIDTH), alternativeNames=['tdata' ])
        self.last = s(alternativeNames=['tlast' ])
        self.ready = s(masterDir=D.IN, alternativeNames=['tready' ])
        self.valid = s(alternativeNames=['tvalid' ])
    
    def _getIpCoreIntfClass(self):
        return IP_AXIStream

class AxiStream(AxiStream_withoutSTRB):
    def _declr(self):
        super(AxiStream, self)._declr()
        self.strb = s(dtype=vecT(self.DATA_WIDTH // 8),
                      alternativeNames=['tstrb'])  # 'keep', 'tkeep'
    
    def _getSimAgent(self):
        return AxiStreamAgent
    
    
class Axi_user(Interface):
    def _config(self):
        self.USER_WIDTH = Param(1)
        
    def _declr(self):
        self.user = s(dtype=vecT(self.USER_WIDTH),
                      alternativeNames=['tuser'])

class AxiStream_withUserAndNoStrb(AxiStream_withoutSTRB, Axi_user):
    def _config(self):
        AxiStream_withoutSTRB._config(self)
        Axi_user._config(self)
    
    def _declr(self):
        AxiStream_withoutSTRB._declr(self)
        Axi_user._declr(self)

class AxiStream_withId(AxiStream):
    def _config(self):
        AxiStream._config(self)
        self.ID_WIDTH = Param(1)
    
    def _declr(self):
        AxiStream._declr(self)
        self.id = s(dtype=vecT(self.ID_WIDTH))
    
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
        
            
class AxiLite_addr(Interface):
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        
    def _declr(self):
        self.addr = s(dtype=vecT(self.ADDR_WIDTH), alternativeNames=['addr_v'])
        self.ready = s(masterDir=D.IN)
        self.valid = s()

    def _getSimAgent(self):
        return AxiLite_addrAgent

class AxiLite_r(Interface):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        
    def _declr(self):
        self.data = s(dtype=vecT(self.DATA_WIDTH), alternativeNames=['data_v'])
        self.resp = s(dtype=vecT(2), alternativeNames=['resp_v'])
        self.ready = s(masterDir=D.IN)
        self.valid = s()

    def _getSimAgent(self):
        return AxiLite_rAgent
    
class AxiLite_w(Interface):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        
    def _declr(self):
        self.data = s(dtype=vecT(self.DATA_WIDTH), alternativeNames=['data_v'])
        self.strb = s(dtype=vecT(self.DATA_WIDTH // 8), alternativeNames=['strb_v'])
        self.ready = s(masterDir=D.IN)
        self.valid = s()
        
    def _getSimAgent(self):
        return AxiLite_wAgent
        
    
class AxiLite_b(Interface):
    def _declr(self):
        self.resp = s(dtype=vecT(2), alternativeNames=['resp_v'])
        self.ready = s(masterDir=D.IN)
        self.valid = s()
    def _getSimAgent(self):
        return AxiLite_bAgent

class AxiLite(Interface):
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        
    def _declr(self):
        with self._paramsShared():
            self.aw = AxiLite_addr()
            self.ar = AxiLite_addr()
            self.w = AxiLite_w()
            self.r = AxiLite_r(masterDir=D.IN)
            self.b = AxiLite_b(masterDir=D.IN)
            
    def _getIpCoreIntfClass(self):
        return IP_AXILite
    
    def _getSimAgent(self):
        return AxiLiteAgent

        
class Axi4_addr(AxiLite_addr):
    def _config(self):
        super(Axi4_addr, self)._config()
        self.ID_WIDTH = Param(3)
    
    def _declr(self):
        super(Axi4_addr, self)._declr()
        self.id = s(dtype=vecT(self.ID_WIDTH), alternativeNames=['id_v'])
        self.burst = s(dtype=vecT(2), alternativeNames=['burst_v'])
        self.cache = s(dtype=vecT(4), alternativeNames=['cache_v'])
        self.len = s(dtype=vecT(8), alternativeNames=['len_v'])
        self.lock = s(dtype=vecT(1), alternativeNames=['lock_v'])
        self.prot = s(dtype=vecT(3), alternativeNames=['prot_v'])
        self.size = s(dtype=vecT(3), alternativeNames=['size_v'])
        self.qos = s(dtype=vecT(4), alternativeNames=['qos_v'])

    def _getSimAgent(self):
        return Axi4_addrAgent

class Axi4_r(AxiLite_r):
    def _config(self):
        super(Axi4_r, self)._config()
        self.ID_WIDTH = Param(3)
    
    def _declr(self):
        super(Axi4_r, self)._declr()
        self.id = s(dtype=vecT(self.ID_WIDTH), alternativeNames=['id_v'])
        self.last = s()
    
    def _getSimAgent(self):
        return Axi4_rAgent
    
class Axi4_w(AxiLite_w):
    def _config(self):
        super(Axi4_w, self)._config()
        self.ID_WIDTH = Param(3)
    
    def _declr(self):
        super(Axi4_w, self)._declr()
        self.id = s(dtype=vecT(self.ID_WIDTH), alternativeNames=['id_v'])
        self.last = s()
    
    
class Axi4_b(AxiLite_b):
    def _config(self):
        super(Axi4_b, self)._config()
        self.ID_WIDTH = Param(3)
    
    def _declr(self):
        super(Axi4_b, self)._declr()
        self.id = s(dtype=vecT(self.ID_WIDTH), alternativeNames=['id_v'])

class Axi4(AxiLite):
    def _config(self):
        super(Axi4, self)._config()
        self.ID_WIDTH = Param(3)
        
    def _declr(self):
        with self._paramsShared():
            self.aw = Axi4_addr()
            self.ar = Axi4_addr()
            self.w = Axi4_w()
            self.r = Axi4_r(masterDir=D.IN)
            self.b = Axi4_b(masterDir=D.IN)
    
    def _getIpCoreIntfClass(self):
        return IP_Axi4


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
            self.r = AxiLite_r_xil(masterDir=D.IN)
            self.b = AxiLite_b_xil(masterDir=D.IN)


class Axi4_addr_xil(Axi4_addr):
    _NAME_SEPARATOR = ''
class Axi4_r_xil(Axi4_r):
    _NAME_SEPARATOR = ''
class Axi4_w_xil(Axi4_w):
    _NAME_SEPARATOR = ''
class Axi4_b_xil(Axi4_b):
    _NAME_SEPARATOR = ''


class Axi4_xil(Axi4):
    def _declr(self):
        with self._paramsShared():
            self.ar = Axi4_addr_xil()
            self.aw = Axi4_addr_xil()
            self.w = Axi4_w_xil()
            self.r = Axi4_r_xil(masterDir=D.IN)
            self.b = Axi4_b_xil(masterDir=D.IN)  
