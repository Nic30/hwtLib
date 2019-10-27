from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.array import HArray
from hwt.hdl.types.struct import HStruct
from pyMathBitPrecise.bit_utils import mask


class PartialField(object):
    """
    HStruct field made from proxy interface
    """

    def __init__(self, originalField):
        self._originalField = originalField
        self.name = originalField.name


class MemorySpaceItem(object):
    """
    Abstraction over place in memory, allows you read
    and write data to/from this space
    """

    def __init__(self, memHandler, transTmpl, offset=0):
        self.memHandler = memHandler
        t = self.transTmpl = transTmpl
        self.myBitAddr = transTmpl.bitAddr + offset
        self.myAddr = self.myBitAddr // memHandler._ADDR_STEP

        self.mask = memHandler._mask(t.bitAddr,
                                     (t.bitAddrEnd - t.bitAddr) // (
                                         self.memHandler._ADDR_STEP * 8))
        self.w_resp = []
        self.r_resp = []

    def _add_write_resp(self, resp):
        self.w_resp.append(resp)

    def _add_read_resp(self, resp):
        self.r_resp.append(resp)

    def write(self, data, onDone=None):
        """
        write data to place in memory
        """
        # t = self.transTmpl
        self.memHandler._write(self.myAddr, 1, data, self.mask, onDone=onDone)

    def read(self, onDone=None):
        """
        read data from place in memory
        """
        self.memHandler._read(self.myAddr, 1, onDone=onDone)


class MemorySpaceItemStruct(object):

    def __init__(self, memHandler, transTmpl, offset=0):
        self._offset = offset
        self._decorateWithRegisters(memHandler, transTmpl)

    def _decorateWithRegisters(self, memHandler, structT):
        """
        Decorate this object with attributes from memory space
        (name is same as specified in register map)

        :param memHandler: instance of AbstractMemSpaceMaster(subclass of)
        :param structT: instance of HStruct or TransTmpl used as template
        """
        if isinstance(structT, TransTmpl):
            tmpl = structT
        else:
            tmpl = TransTmpl(structT)

        for trans in tmpl.children:
            t = trans.dtype
            if isinstance(t, HArray):
                msi = MemorySpaceItemArr(
                    memHandler, trans, offset=self._offset)
            elif isinstance(t, HStruct):
                msi = MemorySpaceItemStruct(
                    memHandler, trans, offset=self._offset)
            else:
                msi = MemorySpaceItem(memHandler, trans, offset=self._offset)

            name = trans.origin.name
            assert not hasattr(self, name), name
            setattr(self, name, msi)


class MemorySpaceItemArr(object):
    """
    Abstraction over place in memory, allows you read and write data
    to/from this space
    """

    def __init__(self, memHandler, transTmpl, offset=0):
        self._offset = transTmpl.bitAddr + offset
        self.memHandler = memHandler
        self.transTmpl = transTmpl
        self.mask = -1
        self.items_cache = [None for _ in range(transTmpl.itemCnt)]
        t = self.transTmpl.dtype.element_t
        if isinstance(t, HStruct):
            self.itemCls = MemorySpaceItemStruct
        elif isinstance(t, HArray):
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
        mi = self.itemCls(m, self.transTmpl.children, offset)
        self.items_cache[index] = mi
        return mi


class AbstractMemSpaceMaster(MemorySpaceItemStruct):
    """
    Abstraction over bus interface which converts it to memory space
    from where you can read or write
    """

    def __init__(self, bus, registerMap):
        self._bus = bus
        self._ADDR_STEP = bus._getAddrStep()
        self._WORD_ADDR_STEP = bus._getWordAddrStep()
        self._DATA_WIDTH = int(bus.DATA_WIDTH)
        self._offset = 0
        self._decorateWithRegisters(self, registerMap)

    def parse_responses(self):
        """
        Parse responses after sim
        """
        raise NotImplementedError(
            "Implement this method in concrete implementation of this class")

    def _mask(self, start, width):
        return mask(width // self._ADDR_STEP)

    def _write(self, addr, size, data, mask, onDone=None):
        """
        Add write transaction to agent of interface

        :param addr: address value on bus to write on
        :param size: size of data to write in bites
        :param data: data to write on bus
        :param onDone: on write done callback function(sim) -> None
        """
        raise NotImplementedError(
            "Implement this method in concrete implementation of this class")

    def _read(self, addr, size, onDone=None):
        """
        Add read transaction to agent of interface
        :param addr: address value on bus to read froms
        :param size: size of data to read in bites
        :param onDone: on read done callback function(sim) -> None

        """
        raise NotImplementedError(
            "Implement this method in concrete implementation of this class")
