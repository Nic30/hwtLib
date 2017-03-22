from hwt.bitmask import mask, selectBitRange
from itertools import chain


class AllocationError(Exception):
    pass


def reshapedInitItems(actualCellSize, requestedCellSize, values):
    if actualCellSize < requestedCellSize and requestedCellSize % actualCellSize == 0:
        itemsInCell = requestedCellSize // actualCellSize
        itemAlign = len(values) % itemsInCell
        if itemAlign != 0:
            values = chain(values, [0 for _ in range(itemsInCell - itemAlign)])
        for itemsInWord in zip(*[iter(values)] * itemsInCell):
            item = 0
            for iIndx, i2 in enumerate(itemsInWord):
                subIndx = itemsInCell - iIndx - 1
                _i2 = (mask(actualCellSize * 8) & i2) << (subIndx * actualCellSize * 8)
                item |= _i2
            yield item
    else:
        raise NotImplementedError()


class DenseMemory():
    """
    Simulation component
    @ivar data: memory dict
    """
    def __init__(self, cellWidth, clk, rDatapumpIntf=None, wDatapumpIntf=None, parent=None):
        """
        @param cellWidth: width of items in memmory
        @param clk: clk signal for synchronization
        @param parent: parent instance of DenseMemory (memory will be shared with this instance)
        """
        assert cellWidth % 8 == 0
        self.cellSize = cellWidth // 8
        self.allMask = mask(self.cellSize)

        self.parent = parent
        if parent is None:
            self.data = {}
        else:
            self.data = parent.data

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
        if self.arAg is not None:
            if self.arAg.data:
                self.onReadReq()

            if self.rPending:
                self.doRead()

        if self.awAg is not None:
            if self.awAg.data:
                self.onWriteReq()

            if self.wPending and self.wPending[0][2] <= len(self.wAg.data):
                self.doWrite()

        return set()

    def parseReq(self, req):
        for i, v in enumerate(req):
            assert v._isFullVld(), (i, v)
        assert len(req) == 4

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

            if data is None:
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

            assert last == isLast, "write 0x%x, size %d, expected last:%d in word %d" % (addr, size, isLast, i)

            if data is None:
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

    def malloc(self, size, keepOut=None):
        """
        Allocates a block of memory of size and initialize it with None (invalid value)
        @param size: Size of each element.
        @param keepOut: space[B] to left between last structure in memory and start of this allocation block
        @return: address of allocated memory
        """
        addr = 0
        k = self.data.keys()
        if k:
            addr = (max(k) + 1) * self.cellSize

        if keepOut:
            addr += keepOut

        indx = addr // self.cellSize
        if indx * self.cellSize != addr:
            NotImplementedError("unaligned allocations not implemented (0x%x)" % addr)

        d = self.data
        for i in range(size // self.cellSize):
            tmp = indx + i

            if tmp in d.keys():
                raise AllocationError("Address 0x%x is already occupied" % (tmp * self.cellSize))

            d[tmp] = None

        return addr

    def calloc(self, num, size, keepOut=None, initValues=None):
        """
        Allocates a block of memory for an array of num elements, each of them
        size bytes long, and initializes all its bits to zero.
        @param num: Number of elements to allocate.
        @param size: Size of each element.
        @return: address of allocated memory
        """
        addr = 0
        k = self.data.keys()
        if k:
            addr = (max(k) + 1) * self.cellSize

        if keepOut:
            addr += keepOut

        indx = addr // self.cellSize
        if indx * self.cellSize != addr:
            NotImplementedError("unaligned allocations not implemented (0x%x)" % addr)

        d = self.data
        wordCnt = (num * size) // self.cellSize

        if initValues is not None:
            if size != self.cellSize:
                initValues = list(reshapedInitItems(size, self.cellSize, initValues))
            assert len(initValues) == wordCnt, (len(initValues), wordCnt)

        for i in range(wordCnt):
            tmp = indx + i

            if tmp in d.keys():
                raise AllocationError("Address 0x%x is already occupied" % (tmp * self.cellSize))
            if initValues is None:
                d[tmp] = 0
            else:
                d[tmp] = initValues[i]

        return addr

    def getArray(self, addr, itemSize, itemCnt):
        """
        Get array stored in memory
        """
        if itemSize != self.cellSize:
            raise NotImplementedError()

        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            raise NotImplementedError("unaligned not implemented")

        out = []
        for i in range(baseIndex, baseIndex + itemCnt):
            try:
                v = self.data[i]
            except KeyError:
                v = None

            out.append(v)
        return out

    def getStruct(self, addr, structT):
        """
        Get HStruct from memory
        """
        cellWidth = self.cellSize * 8
        bitAddr = addr * 8
        s = structT.getValueCls()

        for f in structT.fields:
            fieldLen = f.type.bit_length()

            # resolve value of field from memory
            if f.name is not None:
                fieldOffset = 0
                field = 0
                try:
                    while True:
                        a = bitAddr + fieldOffset
                        indx = a // cellWidth
                        off = a % cellWidth
                        v = self.data[indx]
                        if fieldOffset + cellWidth < fieldLen:
                            bitsLen = cellWidth
                        else:
                            bitsLen = fieldLen - fieldOffset

                        field |= selectBitRange(v, off, bitsLen) << fieldOffset
                        if fieldLen <= fieldOffset + cellWidth:
                            break
                except KeyError:
                    field = None
                setattr(s, f.name, field)

            bitAddr += fieldLen

        return s
