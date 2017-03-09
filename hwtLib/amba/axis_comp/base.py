from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.amba.axis import AxiStream_withoutSTRB


class AxiSCompBase(HandshakedCompBase):
    """
    Abstract base for axis components
    """
    def __init__(self, hsIntfCls):
        """
        @param hsIntfCls: class of interface which should be used as interface of this unit
        """
        assert(issubclass(hsIntfCls, AxiStream_withoutSTRB)), hsIntfCls
        self.intfCls = hsIntfCls
        Unit.__init__(self)
        
    def getVld(self, intf):
        return intf.valid
    
    def getRd(self, intf):
        return intf.ready

    def getDataWidthDependent(self, intf):
        s = []
        s.append(intf.data)

        try:
            s.append(intf.strb)
        except AttributeError:
            pass
        
        try:
            s.append(intf.keep)
        except AttributeError:
            pass
        return s
        