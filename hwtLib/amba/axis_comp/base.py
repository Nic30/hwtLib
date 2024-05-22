from hwt.hwModule import HwModule
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.handshaked.compBase import HandshakedCompBase
from typing import Optional


class Axi4SCompBase(HandshakedCompBase):
    """
    Abstract base for axis components
    """

    def __init__(self, hwIOCls=Axi4Stream, hdlName:Optional[str]=None):
        """
        :param hshwIO: class of interface which should be used as interface of this unit
        """
        self.hwIOCls = hwIOCls
        HwModule.__init__(self, hdlName=hdlName)

    @classmethod
    def get_valid_signal(cls, hwIO):
        return hwIO.valid

    @classmethod
    def get_ready_signal(cls, hwIO):
        return hwIO.ready

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
