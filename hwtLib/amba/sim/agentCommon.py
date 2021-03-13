from hwt.interfaces.agents.handshaked import HandshakedAgent


class BaseAxiAgent(HandshakedAgent):

    @classmethod
    def get_ready_signal(cls, intf):
        return intf.ready._sigInside

    @classmethod
    def get_valid_signal(cls, intf):
        return intf.valid._sigInside
