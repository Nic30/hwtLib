from hwt.bitmask import mask


class DenseMemory():
    """Simulation component"""
    def __init__(self, cellSize, clk, arAg, rAg, awAg, wAg, wAckAg):
        self.cellSize = cellSize
        self.data = {}
        
        self.arAg = arAg  
        self.rAg = rAg   
        self.awAg = awAg  
        self.wAg = wAg   
        self.wAckAg = wAckAg
        
        self.rPending = []
        
        self.wPending = []
        
        self._registerOnClock(clk)
        
    def _registerOnClock(self, clk):
        clk._sigInside.simRisingSensProcs.add(self.checkRequests)
        
    def checkRequests(self, simulator):
        if self.arAg:
            if self.arAg.data:
                self.onReadReq()
                
            if self.rPending:
                self.doRead()
        
        if self.awAg:
            if self.awAg.data:
                self.onWriteReq()
            
            if self.wPending and self.wPending[0][2] <= len(self.wAg.data):
                self.doWrite()
        
        return set()
    
    def parseReq(self, req):
        for i, v in enumerate(req):
            assert v._isFullVld(), (i, v) 
        
        _id = req[0].val
        addr = req[1].val
        size = req[2].val + 1
        if req[3].val == 0:
            lastWordBitmask = mask(self.cellSize // 8)
        else:
            lastWordBitmask = mask(req[3].val)
            size += 1 
        return (_id, addr, size, lastWordBitmask)
        
    def onReadReq(self):
        readReq = self.arAg.data.pop()
        self.rPending.append(self.parseReq(readReq))
         
    def onWriteReq(self):
        writeReq = self.awAg.data.pop()
        self.wPending.append(self.parseReq(writeReq))
    
    def doRead(self):
        _id, addr, size, lastWordBitmask = self.rPending.pop(0)
        
        baseIndex = addr // (self.cellSize // 8)
        if baseIndex * (self.cellSize // 8) != addr:
            raise NotImplementedError("unaligned transaction not implemented")
        
        for i in range(size):
            isLast = i == size - 1
            try:
                data = self.data[baseIndex + i]
            except KeyError:
                data = None
            
            if data == None:
                raise AssertionError("Invalid read of uninitialized value on addr 0x%x" % 
                                     (addr + i * (self.cellSize // 8)))
                
            if isLast:
                strb = lastWordBitmask
            else:
                strb = mask(self.cellSize // 8) 
                   
            self.rAg.data.append((_id, data, strb, isLast))
    
    def doWriteAck(self, _id):
        self.wAckAg.data.append(_id)
            
    def doWrite(self):
        _id, addr, size, lastWordBitmask = self.wPending.pop(0)
        
        baseIndex = addr // (self.cellSize // 8)
        if baseIndex * (self.cellSize // 8) != addr:
            raise NotImplementedError("unaligned transaction not implemented")
        
        for i in range(size):
            data, strb, last = self.wAg.data.pop(0)
            
            assert data._isFullVld()
            assert strb._isFullVld()
            assert last._isFullVld()
            
            data, strb, last = data.val, strb.val, bool(last.val)
            
            isLast = i == size - 1
            
            assert last == isLast
                        
            if data == None:
                raise AssertionError("Invalid read of uninitialized value on addr 0x%x" % 
                                     (addr + i * (self.cellSize // 8)))
                
            if isLast:
                expectedStrb = lastWordBitmask
            else:
                expectedStrb = mask(self.cellSize // 8)

            if expectedStrb != mask(self.cellSize // 8):
                raise NotImplementedError()
            assert strb == expectedStrb
            
            self.data[baseIndex + i] = data
        
        self.doWriteAck(_id)
        
