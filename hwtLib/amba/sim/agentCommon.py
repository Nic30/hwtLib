from hwt.interfaces.agents.handshaked import HandshakedAgent

class BaseAxiAgent(HandshakedAgent):
        
    def getRd(self):
        """get "ready" signal"""
        return self.intf.ready
    
    def getVld(self):
        """get "valid" signal"""
        return self.intf.valid