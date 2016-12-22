from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwtLib.interfaces.amba_constants import BURST_INCR, CACHE_DEFAULT, LOCK_DEFAULT, \
    PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT, RESP_OKAY
from hwt.simulator.agentBase import AgentBase

class BaseAxiAgent(HandshakedAgent):
        
    def getRd(self):
        """get "ready" signal"""
        return self.intf.ready
    
    def getVld(self):
        """get "valid" signal"""
        return self.intf.valid

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

class AxiLite_addrAgent(BaseAxiAgent):
    def doRead(self, s):
        return s.read(self.intf.addr)
    
    def doWrite(self, s, data):
        s.write(data, self.intf.addr)

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
        
class AxiLite_bAgent(BaseAxiAgent):
    def doRead(self, s):
        return s.r(self.intf.resp)
    
    def doWrite(self, s, data):
        s.w(data, self.intf.resp)

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
