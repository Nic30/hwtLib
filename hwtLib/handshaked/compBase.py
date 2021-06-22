from typing import Type, Union, Optional

from hwt.interfaces.std import Handshaked, HandshakeSync
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import walkPhysInterfaces
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class HandshakedCompBase(Unit):
    """
    Abstract class for components which has Handshaked interface as main
    """

    def __init__(self, hsIntfCls: Type[Union[Handshaked, HandshakeSync]],
                 hdl_name_override:Optional[str]=None):
        """
        :param hsIntfCls: class of interface which should be used
            as interface of this unit
        """
        assert(issubclass(hsIntfCls, (Handshaked, HandshakeSync))), hsIntfCls
        self.intfCls = hsIntfCls
        Unit.__init__(self, hdl_name_override=hdl_name_override)

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.intfCls._config(self)

    @classmethod
    def get_valid_signal(cls, intf):
        return intf.vld

    @classmethod
    def get_ready_signal(cls, intf):
        return intf.rd

    def get_data(self, intf):
        rd = self.get_ready_signal(intf)
        vld = self.get_valid_signal(intf)
        return [x for x in walkPhysInterfaces(intf)
                if (x is not rd) and (x is not vld)]
