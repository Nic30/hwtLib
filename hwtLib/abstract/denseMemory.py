from hwt.bitmask import mask


class DenseMemory():
    """Simulation component"""
    def __init__(self, cellWidth, clk, rDatapumpIntf=None, wDatapumpIntf=None):
        assert cellWidth % 8 == 0
        self.cellSize = cellWidth // 8
        self.allMask = mask(self.cellSize)
        
        self.data = {}
        
        assert rDatapumpIntf is not None or wDatapumpIntf is not None
        
        if rDatapumpIntf is None:
            arAg = rAg = None
        else:
            arAg = rDatapumpIntf.req._ag
            rAg = rDatapumpIntf.r._ag
             
        self.arAg = arAg  
        self.rAg = rAg   
        self.rPending = []        
        
        if wDatapumpIntf is None:
            awAg = wAg = wAckAg = None
        else:
            awAg = wDatapumpIntf.req._ag
            wAg = wDatapumpIntf.w._ag
            wAckAg = wDatapumpIntf.ack._ag

        self.awAg = awAg  
        self.wAg = wAg   
        self.wAckAg = wAckAg
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
            lastWordBitmask = self.allMask
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
        
        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            raise NotImplementedError("unaligned transaction not implemented (0x%x)" % addr)
        
        for i in range(size):
            isLast = i == size - 1
            try:
                data = self.data[baseIndex + i]
            except KeyError:
                data = None
            
            if data == None:
                raise AssertionError("Invalid read of uninitialized value on addr 0x%x" % 
                                     (addr + i * self.cellSize))
                
            if isLast:
                strb = lastWordBitmask
            else:
                strb = self.allMask 
                   
            self.rAg.data.append((_id, data, strb, isLast))
    
    def doWriteAck(self, _id):
        self.wAckAg.data.append(_id)
            
    def doWrite(self):
        _id, addr, size, lastWordBitmask = self.wPending.pop(0)
        
        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
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
                                     (addr + i * self.cellSize))
                
            if isLast:
                expectedStrb = lastWordBitmask
            else:
                expectedStrb = self.allMask

            if expectedStrb != self.allMask:
                raise NotImplementedError()
            assert strb == expectedStrb
            
            self.data[baseIndex + i] = data
        
        self.doWriteAck(_id)
        
