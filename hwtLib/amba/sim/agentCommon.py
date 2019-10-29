from hwt.interfaces.agents.handshaked import HandshakedAgent


class BaseAxiAgent(HandshakedAgent):

    def get_ready_signal(self, intf):
        """get "ready" signal"""
        return intf.ready

    def get_valid_signal(self, intf):
        """get "valid" signal"""
        return intf.valid
