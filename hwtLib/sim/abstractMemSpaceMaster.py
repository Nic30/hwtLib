from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.bitmask import mask
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.struct import HStruct


class PartialField(object):
    """
    HStruct field made from proxy interface
    """
    def __init__(self, originalField):
        self._originalField = originalField
        self.name = originalField.name


class MemorySpaceItem(object):
    """
    Abstraction over place in memory, allows you read and write data to/from this space
    """
    def __init__(self, memHandler, transTmpl, offset=0):
        self.memHandler = memHandler
        t = self.transTmpl = transTmpl
        self.myBitAddr = transTmpl.bitAddr + offset 
        self.myAddr = self.myBitAddr // memHandler._ADDR_STEP
        
        self.mask = memHandler._mask(t.bitAddr,
                                    (t.bitAddrEnd - t.bitAddr) // self.memHandler._ADDR_STEP // 8)

    def write(self, data):
        """
        write data to place in memory
        """
        m = self.memHandler
        # t = self.transTmpl
        m._write(self.myAddr , 1, data, self.mask)

    def read(self):
        """
        read data from place in memory
        """
        m = self.memHandler
        m._read(self.myAddr, 1)


class MemorySpaceItemStruct(object):
    def __init__(self, memHandler, transTmpl, offset=0):
        self._offset = offset
        self._decorateWithRegisters(memHandler, transTmpl)

    def _decorateWithRegisters(self, memHandler, structT):
        """
        Decorate this object with attributes from memory space (name is same as specified in register map)
        
        :param memHandler: instance of AbstractMemSpaceMaster(subclass of)
        :param structT: instance of HStruct or TransTmpl used as template
        """
        if isinstance(structT, TransTmpl):
            tmpl = structT
        else:
            tmpl = TransTmpl(structT)

        for trans in tmpl.children:
            t = trans.dtype
            if isinstance(t, Array):
                msi = MemorySpaceItemArr(memHandler, trans, offset=self._offset)
            elif isinstance(t, HStruct):
                msi = MemorySpaceItemStruct(memHandler, trans, offset=self._offset)
            else:
                msi = MemorySpaceItem(memHandler, trans, offset=self._offset)

            name = trans.origin.name
            assert not hasattr(self, name), name
            setattr(self, name, msi)

class MemorySpaceItemArr(object):
    """
    Abstraction over place in memory, allows you read and write data to/from this space
    """
    def __init__(self, memHandler, transTmpl, offset=0):
        self._offset = transTmpl.bitAddr + offset
        self.memHandler = memHandler
        self.transTmpl = transTmpl
        self.mask = -1
        self.items_cache = [None for _ in range(transTmpl.itemCnt)]
        t = self.transTmpl.dtype.elmType
        if isinstance(t, HStruct):
            self.itemCls = MemorySpaceItemStruct
        elif isinstance(t, Array):
            self.itemCls = MemorySpaceItemArr
        else:
            self.itemCls = MemorySpaceItem
        
        self.itemSize = transTmpl.children.bit_length()
            
    def __getitem__(self, index):
        # tTmpl = self.transTmpl
        item = self.items_cache[index]
        if item is not None:
            return item

        m = self.memHandler
        offset = self._offset + self.itemSize * index
        mi = self.itemCls(self.memHandler, self.transTmpl.children, offset)
        self.items_cache[index] = mi
        return mi


class AbstractMemSpaceMaster(MemorySpaceItemStruct):
    """
    Abstraction over bus interface which converts it to memory space from where you can read or write
    """
    def __init__(self, bus, registerMap):
        self._bus = bus
        self._ADDR_STEP = bus._getAddrStep()
        self._WORD_ADDR_STEP = bus._getWordAddrStep()
        self._DATA_WIDTH = int(bus.DATA_WIDTH)
        self._offset = 0
        self._decorateWithRegisters(self, registerMap)

    def _mask(self, start, width):
        return mask(width // self._ADDR_STEP)

    def _write(self, addr, size, data, mask):
        raise NotImplementedError("Implement this method in concrete implementation of this class")

    def _read(self, addr, size):
        raise NotImplementedError("Implement this method in concrete implementation of this class")
