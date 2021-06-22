from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.handshaked.compBase import HandshakedCompBase
from typing import Optional


class AxiSCompBase(HandshakedCompBase):
    """
    Abstract base for axis components
    """

    def __init__(self, intfCls=AxiStream, hdl_name_override:Optional[str]=None):
        """
        :param hsIntfCls: class of interface which should be used as interface of this unit
        """
        self.intfCls = intfCls
        Unit.__init__(self, hdl_name_override=hdl_name_override)

    @classmethod
    def get_valid_signal(cls, intf):
        return intf.valid

    @classmethod
    def get_ready_signal(cls, intf):
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
