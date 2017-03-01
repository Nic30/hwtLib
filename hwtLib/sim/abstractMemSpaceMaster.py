
class MemorySpaceItem(object):
    """
    Abstraction over place in memory, allows you read and write data to/from this space
    """
    def __init__(self, memHandler, addrSpaceItem):
        self.memHandler = memHandler
        self.addrSpaceItem = addrSpaceItem
        self.mask = -1

    def write(self, data, thenFn=None):
        """
        write data to place in memory
        @param thenFn: callback function with single parameter: readedData
        """
        asi = self.addrSpaceItem
        self.memHandler._write(asi.addr, asi.size, data, self.mask, thenFn=thenFn)

    def read(self, thenFn):
        """
        read data from place in memory
        @param thenFn: callback function with single parameter: readedData
        """
        asi = self.addrSpaceItem
        self.memHandler._write(asi.addr, asi.size, thenFn=thenFn)


class AbstractMemSpaceMaster(object):
    """
    Abstraction over bus interface which converts it to memory space from where you can read or write
    """
    def __init__(self, bus, registerMap):
        self._bus = bus
        self._decorateWithRegisters(registerMap)

    def _decorateWithRegisters(self, registerMap):
        """
        Decorate this object with attributes from memory space (name is same as specified in register map)
        """
        for addrSpaceItem in registerMap.values():
            msi = MemorySpaceItem(self, addrSpaceItem)
            name = addrSpaceItem.name
            assert not hasattr(self, name)
            setattr(self, name, msi)

    def _write(self, addr, size, data, mask, thenFn=None):
        raise NotImplementedError("Implement this method in concrete implementation of this class")

    def _read(self, addr, size, thenFn):
        raise NotImplementedError("Implement this method in concrete implementation of this class")
