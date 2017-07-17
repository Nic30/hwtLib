from itertools import chain

from hwt.bitmask import mask, selectBitRange
from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.struct import HStruct
from hwt.simulator.types.simBits import simBitsT
from collections import deque


class AllocationError(Exception):
    """
    Exception which says that requested allocation can not be performed
    """
    pass


def reshapedInitItems(actualCellSize, requestedCellSize, values):
    """
    Convert array item size and items cnt while size of array remains unchanged

    :param actualCellSize: actual size of item in array
    :param requestedCellSize: requested size of item in array
    :param values: input array
    :return: generator of new items of specified characteristik
    """
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
        raise NotImplementedError("Reshaping of array from cell size %d to %d" % (actualCellSize, requestedCellSize))


class DenseMemory():
    """
    Dense memory for simulation purposes with datapump interfaces

    :ivar data: memory dict
    """
    def __init__(self, cellWidth, clk, rDatapumpIntf=None, wDatapumpIntf=None, parent=None):
        """
        :param cellWidth: width of items in memmory
        :param clk: clk signal for synchronization
        :param parent: parent instance of DenseMemory (memory will be shared with this instance)
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
        self.rPending = deque()

        if wDatapumpIntf is None:
            awAg = wAg = wAckAg = None
        else:
            awAg = wDatapumpIntf.req._ag
            wAg = wDatapumpIntf.w._ag
            wAckAg = wDatapumpIntf.ack._ag

        self.awAg = awAg
        self.wAg = wAg
        self.wAckAg = wAckAg
        self.wPending = deque()

        self._registerOnClock(clk)

    def _registerOnClock(self, clk):
        clk._sigInside.simRisingSensProcs.add(self.checkRequests)

    def checkRequests(self, simulator, _):
        """
        Check if any request has appeared on interfaces
        """
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
        _id, addr, size, lastWordBitmask = self.rPending.popleft()

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
        _id, addr, size, lastWordBitmask = self.wPending.popleft()

        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            raise NotImplementedError("unaligned transaction not implemented")

        for i in range(size):
            data, strb, last = self.wAg.data.popleft()

            # assert data._isFullVld()
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

        :param size: Size of each element.
        :param keepOut: optional memory spacing between this memory region and lastly allocated
        :return: address of allocated memory
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

        :param num: Number of elements to allocate.
        :param size: Size of each element.
        :param keepOut: optional memory spacing between this memory region and lastly allocated
        :return: address of allocated memory
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

    def getBits(self, start, end):
        """
        Gets value of bits between selected range from memory
        
        :param start: bit address of start of bit of bits
        :param end: bit address of first bit behind bits
        :return: instance of BitsVal (derived from SimBits type) which contains copy of selected bits
        """
        wordWidth = self.cellSize * 8
        
        inFieldOffset = 0
        allMask = mask(wordWidth)
        value = simBitsT(end - start, None).fromPy(None)

        while start != end:
            assert start < end, (start, end)
      
            dataWordIndex = start // wordWidth 
            v = self.data.get(dataWordIndex, None)
            
            endOfWord = (dataWordIndex + 1) * wordWidth
            width = min(end, endOfWord) - start
            offset = start % wordWidth
            if v is None:
                val = 0
                vldMask = 0
                updateTime = -1
            elif isinstance(v, int):
                val = selectBitRange(v, offset, width)
                vldMask = allMask
                updateTime = -1
            else:
                val = selectBitRange(v.val, offset, width)
                vldMask = selectBitRange(v.vldMask, offset, width)
                updateTime = v.updateTime
                
            m = mask(width)
            value.val |= (val & m) << inFieldOffset
            value.vldMask |= (vldMask & m) << inFieldOffset
            value.updateMask = max(value.updateTime, updateTime) 
                        
            inFieldOffset += width
            start += width

        return value
    
    def _getStruct(self, offset, transTmpl):
        """
        :param offset: global offset of this transTmpl (and struct)
        :param transTmpl: instance of TransTmpl which specifies items in struct
        """
        dataDict = {}
        for subTmpl in transTmpl.children:
            t = subTmpl.dtype
            name = subTmpl.origin.name
            if isinstance(t, Bits):
                value = self.getBits(subTmpl.bitAddr + offset, subTmpl.bitAddrEnd + offset)
            elif isinstance(t, Array):
                raise NotImplementedError()
            elif isinstance(t, HStruct):
                value = self._getStruct(offset, subTmpl)
            else:
                raise NotImplementedError(t)

            dataDict[name] = value    
        
        return transTmpl.dtype.fromPy(dataDict)
         
    def getStruct(self, addr, structT, bitAddr=None):
        """
        Get HStruct from memory
        
        :param addr: address where get struct from
        :param structT: instance of HStruct or FrameTemplate generated from it to resove structure of data
        :param bitAddr: optional bit precisse address is is not None param addr has to be None
        """
        if bitAddr is None:
            assert bitAddr is None
            bitAddr = addr * 8
        else:
            assert addr is not None
        
        if isinstance(structT, TransTmpl):
            transTmpl = structT
            structT = transTmpl.origin
        else:
            assert isinstance(structT, HStruct)
            transTmpl = TransTmpl(structT)
        
        return self._getStruct(bitAddr, transTmpl)
