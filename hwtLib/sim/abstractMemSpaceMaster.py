
class MemorySpaceItem(object):
    """
    Abstraction over place in memory, allows you read and write data to/from this space
    """
    def __init__(self, memHandler, addrSpaceItem):
        self.memHandler = memHandler
        self.addrSpaceItem = addrSpaceItem
        self.mask = -1

    def write(self, data):
        """
        write data to place in memory
        """
        asi = self.addrSpaceItem
        self.memHandler._write(asi.addr, asi.size, data, self.mask)

    def read(self):
        """
        read data from place in memory
        """
        asi = self.addrSpaceItem
        self.memHandler._write(asi.addr, asi.size)


class MemorySpaceItemArr(object):
    """
    Abstraction over place in memory, allows you read and write data to/from this space
    """
    def __init__(self, memHandler, addrSpaceItem):
        self.memHandler = memHandler
        self.addrSpaceItem = addrSpaceItem
        self.mask = -1

    def write(self, index, data):
        """
        write data to place in memory

        :param index: index of item in this array
        """
        asi = self.addrSpaceItem
        if index > asi.size or index < 0:
            raise IndexError(index)
        self.memHandler._write(asi.addr + self.memHandler.WORD_ADDR_STEP * index,
                               1, data, self.mask)

    def read(self, index):
        """
        read data from place in memory

        :param index: index of item in this array
        """
        asi = self.addrSpaceItem
        if index > asi.size or index < 0:
            raise IndexError(index)
        self.memHandler._read(asi.addr + self.memHandler.WORD_ADDR_STEP * index,
                              asi.size)


class AbstractMemSpaceMaster(object):
    """
    Abstraction over bus interface which converts it to memory space from where you can read or write
    """
    def __init__(self, bus, registerMap):
        self._bus = bus
        self.ADDR_STEP = bus._getAddrStep()
        self.WORD_ADDR_STEP = bus._getWordAddrStep()
        self._decorateWithRegisters(registerMap)

    def _decorateWithRegisters(self, registerMap):
        """
        Decorate this object with attributes from memory space (name is same as specified in register map)
        """
        for addrSpaceItem in registerMap.values():
            if addrSpaceItem.size is not None:
                msi = MemorySpaceItemArr(self, addrSpaceItem)
            else:
                msi = MemorySpaceItem(self, addrSpaceItem)
            name = addrSpaceItem.name
            assert not hasattr(self, name)
            setattr(self, name, msi)

    def _write(self, addr, size, data, mask):
        raise NotImplementedError("Implement this method in concrete implementation of this class")

    def _read(self, addr, size):
        raise NotImplementedError("Implement this method in concrete implementation of this class")
