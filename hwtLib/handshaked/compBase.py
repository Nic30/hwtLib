from hwt.interfaces.std import Handshaked, HandshakeSync
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.unit import Unit


class HandshakedCompBase(Unit):
    """
    Abstract class for components which has Handshaked interface as main
    """

    def __init__(self, hsIntfCls):
        """
        :param hsIntfCls: class of interface which should be used
            as interface of this unit
        """
        assert(issubclass(hsIntfCls, (Handshaked, HandshakeSync))), hsIntfCls
        self.intfCls = hsIntfCls
        Unit.__init__(self)

    def _config(self):
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
        return list(where(intf._interfaces, lambda x: (x is not rd) and (x is not vld)))
