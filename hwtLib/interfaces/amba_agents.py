from hdl_toolkit.interfaces.agents.handshaked import HandshakedAgent
from hwtLib.interfaces.amba_constants import BURST_INCR, CACHE_DEFAULT, LOCK_DEFAULT, \
    PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT

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
                                       size=BYTES_IN_TRANS(64),
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

class Axi4_rAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        _id = r(intf.valid)
        data = r(intf.data)
        resp = r(intf.resp)
        last = r(intf.last)
        
        return (_id, data, resp, last)
    
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
        
        data, strb, last = data
        
        w(data, intf.data)
        w(strb, intf.resp)
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
        w(strb, intf.resp)
        w(user, intf.user)
        w(last, intf.last)              
