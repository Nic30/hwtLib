

class DenseMemory():
    """Simulation component"""
    def __init__(self, cellCnt, cellSize, arAg, rAg, awAg, wAg, wAckAg):
        self.cellCnt = cellCnt
        self.cellSize = cellSize
        self.data = {}
        
        self.arAg = arAg  
        self.rAg = rAg   
        self.awAg = awAg  
        self.wAg = wAg   
        self.wAckAg = wAckAg
        
        self.rPending = 0
        self.wPending = 0
    
    
    def checkRequests(self):
        if self.arAg.data:
            readReq = self.arAg.data.pop()
            self.onReadReq(readReq)
            
        if self.awAg.data:
            readReq = self.arAg.data.pop()
            self.onReadReq(readReq)
            
        if self.rPending:
            self.doRead()
        
        if self.wPending:
            self.doWrite()
            
            
    
    def onReadReq(self, readReq):
        raise NotImplementedError()
    
    def onWriteReq(self, writeReq):
        raise NotImplementedError()
    
    def doRead(self):
        raise NotImplementedError()
