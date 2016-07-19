from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.std import Handshaked, HandshakeSync
from python_toolkit.arrayQuery import where


class HandshakedCompBase(Unit):
    
    def __init__(self, hsIntfCls):
        """
        @param hsIntfCls: class of interface which should be used as interface of this unit
        """
        assert(issubclass(hsIntfCls, (Handshaked, HandshakeSync)))
        self.intCls = hsIntfCls
        Unit.__init__(self)
    
    def _config(self):
        self.intCls._config(self)
    
    def getVld(self, intf):
        return intf.vld
    
    def getRd(self, intf):
        return intf.rd
    
    def getData(self, intf):
        rd = self.getRd(intf)
        vld = self.getVld(intf)
        return list(where(intf._interfaces, lambda x: (x is not rd) and (x is not vld)))
