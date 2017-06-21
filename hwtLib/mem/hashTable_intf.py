from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, Signal, HandshakeSync
from hwt.synthesizer.param import Param


class InsertPortAgent(HandshakedAgent):
    """
    Simulation agent for `.InsertPort` interface
    
    data format:
        * if interface has data signal, data format is tuple (hash, key, data, vldFlag)
        * if interface does not have data signal, data format is tuple (hash, key, vldFlag)
    """
    def __init__(self, intf):
        HandshakedAgent.__init__(self, intf)
        self.hasData = bool(intf.DATA_WIDTH)

    def doRead(self, s):
        r = s.read
        i = self.intf
        _hash = r(i.hash)
        key = r(i.key)
        vldFlag = r(i.vldFlag)

        if self.hasData:
            data = r(i.data)
            return hash, key, data, vldFlag
        else:
            return hash, key, vldFlag

    def doWrite(self, s, data):
        w = s.write
        i = self.intf

        if data is None:
            w(None, i.hash)
            w(None, i.key)
            if self.hasData:
                w(None, i.data)
            w(None, i.vldFlag)
        else:
            if self.hasData:
                _hash, key, _data, vldFlag = data
                w(_data, i.data)
            else:
                _hash, key, vldFlag = data

            w(_hash, i.hash)
            w(key, i.key)
            w(vldFlag, i.vldFlag)


class InsertIntf(HandshakeSync):
    def _config(self):
        self.HASH_WIDTH = Param(8)
        self.KEY_WIDTH = Param(8)
        self.DATA_WIDTH = Param(0)

    def _declr(self):
        super(InsertIntf, self)._declr()
        self.hash = VectSignal(self.HASH_WIDTH)
        self.key = VectSignal(self.KEY_WIDTH)
        if self.DATA_WIDTH:
            self.data = VectSignal(self.DATA_WIDTH)
        
        self.vldFlag = Signal()
    
    def _getSimAgent(self):
        return InsertPortAgent


class LookupKeyIntfAgent(HandshakedAgent):
    """
    Simulation agent for LookupKeyIntf interface
    """
    def doRead(self, s):
        return s.read(self.intf.key)
    
    def doWrite(self, s, data):
        s.write(data, self.intf.key)


class LookupKeyIntf(HandshakeSync):
    def _config(self):
        self.KEY_WIDTH = Param(8)

    def _declr(self):
        HandshakeSync._declr(self)
        self.key = VectSignal(self.KEY_WIDTH)

    def _getSimAgent(self):
        return LookupKeyIntfAgent


class LookupResultIntfAgent(HandshakedAgent):
    """
    Simulation agent for `.LookupResultIntf` 
    data is stored in .data 
    data format is tuple (hash, key, data, found) but some items can be missing depending on configuration of interface
    """
    def __init__(self, intf):
        HandshakedAgent.__init__(self, intf)
        self.hasHash = bool(intf.LOOKUP_HASH)
        self.hasKey = bool(intf.LOOKUP_KEY)
        self.hasData = bool(intf.DATA_WIDTH)
        
    def doRead(self, s):
        r = s.read
        d = []
        append = d.append
        intf = self.intf

        if self.hasHash:
            append(r(intf.hash))

        if self.hasKey:
            append(r(intf.key))

        if self.hasHash:
            append(r(intf.data))

        append(r(intf.found))

        return tuple(d)
    
    def doWrite(self, s, data):
        w = s.write
        intf = self.intf
        
        dIt = iter(data)
        
        if self.hasHash:
            w(next(dIt), intf.hash)

        if self.hasKey:
            w(next(dIt), intf.key)

        if self.hasHash:
            w(next(dIt), intf.data)

        w(next(dIt), intf.found)
        
        try:
            next(dIt)
            assert False, "To many items in data %r" % data
        except IndexError:
            return 

class LookupResultIntf(Handshaked):
    """
    Interface for result of lookup in hash table

    :ivar HASH_WIDTH: width of the hash used by hash table
    :ivar KEY_WIDTH: width of the key used by hash table
    :ivar LOOKUP_HASH: flag if this interface should have hash signal
    :ivar LOOKUP_KEY: flag if this interface should have hash signal
    """
    def _config(self):
        self.HASH_WIDTH = Param(8)
        self.KEY_WIDTH = Param(8)
        self.DATA_WIDTH = Param(0)
        self.LOOKUP_HASH = Param(False)
        self.LOOKUP_KEY = Param(False)

    def _declr(self):
        HandshakeSync._declr(self)

        if self.LOOKUP_HASH: 
            self.hash = VectSignal(self.HASH_WIDTH)

        if self.LOOKUP_KEY:
            self.key = VectSignal(self.KEY_WIDTH)

        if self.DATA_WIDTH:
            self.data = VectSignal(self.DATA_WIDTH)

        self.found = Signal()

    def _getSimAgent(self):
        return LookupResultIntfAgent