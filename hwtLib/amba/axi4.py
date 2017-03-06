from hwt.hdlObjects.constants import DIRECTION
from hwt.synthesizer.param import Param, evalParam
from hwtLib.amba.axiLite import AxiLite, AxiLite_b, AxiLite_w, AxiLite_r,\
    AxiLite_addr, IP_AXILite
from hwt.interfaces.std import VectSignal, Signal
from hwtLib.amba.axis import AxiStream_withIdAgent
from hwtLib.amba.constants import RESP_OKAY, BURST_INCR, CACHE_DEFAULT,\
    LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtLib.amba.axi_intf_common import AxiMap, Axi_id


#####################################################################
class Axi4_addr(AxiLite_addr, Axi_id):
    def _config(self):
        AxiLite_addr._config(self)
        Axi_id._config(self)
        self.LEN_WIDTH = 8
        self.LOCK_WIDTH = Param(1)

    def _declr(self):
        AxiLite_addr._declr(self)
        Axi_id._declr(self)
        self.burst = VectSignal(2)
        self.cache = VectSignal(4)
        self.len = VectSignal(self.LEN_WIDTH)
        self.lock = VectSignal(evalParam(self.LOCK_WIDTH).val)
        self.prot = VectSignal(3)
        self.size = VectSignal(3)
        self.qos = VectSignal(4)

    def _getSimAgent(self):
        return Axi4_addrAgent


class Axi4_addrAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        addr = r(intf.addr)
        _id = r(intf.id)
        burst = r(intf.burst)
        cache = r(intf.cache)
        _len = r(intf.len)
        lock = r(intf.lock)
        prot = r(intf.prot)
        size = r(intf.size)
        qos = r(intf.qos)

        return (_id, addr, burst, cache, _len, lock, prot, size, qos)

    def mkReq(self, addr, _len, _id=0, burst=BURST_INCR,
                                       cache=CACHE_DEFAULT,
                                       lock=LOCK_DEFAULT,
                                       prot=PROT_DEFAULT,
                                       size=BYTES_IN_TRANS(8),
                                       qos=QOS_DEFAULT):

        return (_id, addr, burst, cache, _len, lock, prot, size, qos)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.w

        if data is None:
            data = [None for _ in range(9)]

        _id, addr, burst, cache, _len, lock, prot, size, qos = data

        w(_id, intf.id)
        w(addr, intf.intf)
        w(burst, intf.burst)
        w(cache, intf.cache)
        w(_len, intf.len)
        w(lock, intf.lock)
        w(prot, intf.prot)
        w(size, intf.size)
        w(qos, intf.qos)


class Axi4_addr_withUserAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        addr = r(intf.addr)
        _id = r(intf.id)
        burst = r(intf.burst)
        cache = r(intf.cache)
        _len = r(intf.len)
        lock = r(intf.lock)
        prot = r(intf.prot)
        size = r(intf.size)
        qos = r(intf.qos)
        user = r(intf.user)
        return (_id, addr, burst, cache, _len, lock, prot, size, qos, user)

    def mkReq(self, addr, _len, _id=0, burst=BURST_INCR,
                                       cache=CACHE_DEFAULT,
                                       lock=LOCK_DEFAULT,
                                       prot=PROT_DEFAULT,
                                       size=BYTES_IN_TRANS(8),
                                       qos=QOS_DEFAULT,
                                       user=0):
        
        return (_id, addr, burst, cache, _len, lock, prot, size, qos, user)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.w
        
        if data is None:
            data = [None for _ in range(10)]

        _id, addr, burst, cache, _len, lock, prot, size, qos, user = data

        w(_id, intf.id)
        w(addr, intf.intf)
        w(burst, intf.burst)
        w(cache, intf.cache)
        w(_len, intf.len)
        w(lock, intf.lock)
        w(prot, intf.prot)
        w(size, intf.size)
        w(qos, intf.qos)
        w(user, intf.user)

#####################################################################
class Axi4_r(AxiLite_r, Axi_id):
    def _config(self):
        AxiLite_r._config(self)
        Axi_id._config(self)
        
    def _declr(self):
        Axi_id._declr(self)
        AxiLite_r._declr(self)
        self.last = Signal()
    
    def _getSimAgent(self):
        return Axi4_rAgent

class Axi4_rAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        _id = r(intf.valid)
        data = r(intf.data)
        resp = r(intf.resp)
        last = r(intf.last)
        
        return (_id, data, resp, last)
    
    def addData(self, data, _id=0, resp=RESP_OKAY, last=True):
        self.data.append((_id, data, resp, last))
    
    def doWrite(self, s, data):
        intf = self.intf
        w = s.w
        
        if data is None:
            data = [None for _ in range(4)]
        
        _id, data, resp, last = data
        
        w(_id, intf.id)
        w(data, intf.data)
        w(resp, intf.resp)
        w(last, intf.last)
#####################################################################    
class Axi4_w(AxiLite_w, Axi_id):
    def _config(self):
        AxiLite_w._config(self)
        Axi_id._config(self)
        
    def _declr(self):
        Axi_id._declr(self)
        AxiLite_w._declr(self)
        self.last = Signal()
    
    def _getSimAgent(self):
        return AxiStream_withIdAgent

#####################################################################    
class Axi4_b(AxiLite_b, Axi_id):
    def _config(self):
        AxiLite_b._config(self)
        Axi_id._config(self)
    
    def _declr(self):
        Axi_id._declr(self)
        AxiLite_b._declr(self)

    def _getSimAgent(self):
        return Axi4_bAgent


class Axi4_bAgent(BaseAxiAgent):
    def doRead(self, s):
        r = s.r
        intf = self.intf
        
        return r(intf.id), r(intf.resp)
    
    def doWrite(self, s, data):
        w = s.write
        intf = self.intf
        
        if data is None:
            data = [None for _ in range(2)]
        
        _id, resp = data
        
        w(_id, intf.id)
        w(resp, intf.resp)
        

#####################################################################

class Axi4(AxiLite):
    def _config(self):
        AxiLite._config(self)
        self.ID_WIDTH = Param(6)
        self.LOCK_WIDTH = Param(1)
        
    def _declr(self):
        with self._paramsShared():
            self.aw = Axi4_addr()
            self.ar = Axi4_addr()
            self.w = Axi4_w()
            self.r = Axi4_r(masterDir=DIRECTION.IN)
            self.b = Axi4_b(masterDir=DIRECTION.IN)
    
    def _getIpCoreIntfClass(self):
        return IP_Axi4



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
            self.r = Axi4_r_xil(masterDir=DIRECTION.IN)
            self.b = Axi4_b_xil(masterDir=DIRECTION.IN)  




class IP_Axi4(IP_AXILite):
    def __init__(self,):
        super().__init__()
        A_SIGS = ['id', 'burst', 'cache', 'len', 'lock', 'prot', 'size', 'qos']
        AxiMap('ar', A_SIGS, self.map['ar'])
        AxiMap('aw', A_SIGS, self.map['aw'])
        AxiMap('b', ['id'], self.map['b'])
        AxiMap('r', ['id', 'last'], self.map['r'])
        AxiMap('w', ['id', 'last'], self.map['w'])
                     
    def postProcess(self, component, entity, allInterfaces, thisIf):
        self.endianness = "little"
        param = lambda name, val :  self.addSimpleParam(thisIf, name, str(val))
        param("ADDR_WIDTH", thisIf.aw.addr._dtype.bit_length())  # [TODO] width expression
        param("MAX_BURST_LENGTH", 256)
        param("NUM_READ_OUTSTANDING", 5)
        param("NUM_WRITE_OUTSTANDING", 5)
        param("PROTOCOL", "AXI4")
        param("READ_WRITE_MODE", "READ_WRITE")
        param("SUPPORTS_NARROW_BURST", 0)
