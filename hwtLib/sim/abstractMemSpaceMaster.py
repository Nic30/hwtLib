from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.hdlObjects.types.array import Array

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
        self.transTmpl = transTmpl
        self.mask = -1
        self.myAddr = transTmpl.bitAddr + offset

    def write(self, data):
        """
        write data to place in memory
        """
        m = self.memHandler
        m._write(self.myAddr // m.ADDR_STEP, 1, data, self.mask)

    def read(self):
        """
        read data from place in memory
        """
        m = self.memHandler
        m._read(self.myAddr // m.ADDR_STEP, 1)


class MemorySpaceItemArr(object):
    """
    Abstraction over place in memory, allows you read and write data to/from this space
    """
    def __init__(self, memHandler, transTmpl):
        self.memHandler = memHandler
        self.transTmpl = transTmpl
        self.mask = -1

    def __getitem__(self, index):
        tTmpl = self.transTmpl
        if index > tTmpl.itemCnt or index < 0:
            raise IndexError(index)

        m = self.memHandler
        offset = m.WORD_ADDR_STEP * index * m.ADDR_STEP
        return MemorySpaceItem(self.memHandler, self.transTmpl, offset)
        

class AbstractMemSpaceMaster(object):
    """
    Abstraction over bus interface which converts it to memory space from where you can read or write
    """
    def __init__(self, bus, registerMap):
        self._bus = bus
        self.ADDR_STEP = bus._getAddrStep()
        self.WORD_ADDR_STEP = bus._getWordAddrStep()
        self._decorateWithRegisters(registerMap)

    def _decorateWithRegisters(self, stuctT):
        """
        Decorate this object with attributes from memory space (name is same as specified in register map)
        """
        tmpl = TransTmpl(stuctT)
        for trans in tmpl.children:
            if isinstance(trans.dtype, Array):
                msi = MemorySpaceItemArr(self, trans)
            else:
                msi = MemorySpaceItem(self, trans)
            name = trans.origin.name
            assert not hasattr(self, name), name
            setattr(self, name, msi)

    def _write(self, addr, size, data, mask):
        raise NotImplementedError("Implement this method in concrete implementation of this class")

    def _read(self, addr, size):
        raise NotImplementedError("Implement this method in concrete implementation of this class")
