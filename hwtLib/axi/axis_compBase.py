from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.amba import AxiStream_withoutSTRB
from hwtLib.handshaked.compBase import HandshakedCompBase

class AxiSCompBase(HandshakedCompBase):
    def __init__(self, hsIntfCls):
        """
        @param hsIntfCls: class of interface which should be used as interface of this unit
        """
        assert(issubclass(hsIntfCls, AxiStream_withoutSTRB))
        self.intfCls = hsIntfCls
        Unit.__init__(self)
        
    def getVld(self, intf):
        return intf.valid
    
    def getRd(self, intf):
        return intf.ready