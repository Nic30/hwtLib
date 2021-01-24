from math import ceil

from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.pyUtils.arrayQuery import grouper
from pyMathBitPrecise.bit_utils import mask, get_bit_range, int_list_to_int
from hwt.math import shiftIntArray


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
    :return: generator of new items of specified characteristic
    """
    if (actualCellSize < requestedCellSize
            and requestedCellSize % actualCellSize == 0):
        itemsInCell = requestedCellSize // actualCellSize
        for itemsInWord in grouper(itemsInCell, values, padvalue=0):
            yield int_list_to_int(itemsInWord, actualCellSize * 8)
    else:
        raise NotImplementedError(
            f"Reshaping of array from cell size {actualCellSize:d} to {requestedCellSize:d}")


class SimRam():
    """
    Dense memory for simulation purposes with data pump interfaces

    :ivar ~.data: memory dict
    """

    def __init__(self, cellSize, parent=None):
        """
        :param cellWidth: width of items in memory
        :param clk: clk signal for synchronization
        :param parent: parent instance of SimRam
                       (memory will be shared with this instance)
        """

        self.parent = parent
        if parent is None:
            self.data = {}
        else:
            self.data = parent.data
        self.cellSize = cellSize
        self.prevAllocatedAddrEnd = 0

    def malloc(self, size, keepOut=None):
        """
        Allocates a block of memory of size and initialize it
        with None (invalid value)

        :param size: Size of memory block to allocate.
        :param keepOut: optional memory spacing between this memory region
                        and lastly allocated
        :return: address of allocated memory
        """
        addr = self.prevAllocatedAddrEnd
        k = self.data.keys()
        if k:
            addr = (max(k) + 1) * self.cellSize

        if keepOut:
            addr += keepOut

        indx = addr // self.cellSize
        if indx * self.cellSize != addr:
            NotImplementedError(
                f"unaligned allocations not implemented (0x{addr:x})")

        d = self.data
        for i in range(size // self.cellSize):
            tmp = indx + i

            if tmp in d.keys():
                raise AllocationError(
                    "Address 0x%x is already occupied" % (tmp * self.cellSize))

            d[tmp] = None

        self.prevAllocatedAddrEnd = addr
        return addr

    def calloc(self, num, size, keepOut=None, initValues=None) -> int:
        """
        Allocates a block of memory for an array of num elements, each of them
        size bytes long, and initializes all its bits to zero.

        :param num: Number of elements to allocate.
        :param size: Size of each element.
        :param keepOut: optional memory spacing between this memory region
                        and lastly allocated (number of bit between last allocated segment to avoid)
        :param initValues: iterable of word values to init memory with
        :return: address (byte step) of allocated memory
        """
        addr = self.prevAllocatedAddrEnd
        k = self.data.keys()
        if k:
            addr = (max(k) + 1) * self.cellSize

        if keepOut:
            addr += keepOut

        indx = addr // self.cellSize
        shift = addr % self.cellSize
        wordCnt = ceil((num * size) / self.cellSize)
        if shift:
            # shift all data in init values
            initValues = shiftIntArray(initValues, self.cellSize * 8, shift * 8)
            wordCnt += 1

        d = self.data

        if initValues is not None:
            if size != self.cellSize:
                initValues = list(reshapedInitItems(
                    size, self.cellSize, initValues))
            assert len(initValues) == wordCnt, (len(initValues), wordCnt)

        for i in range(wordCnt):
            tmp = indx + i

            if tmp in d.keys():
                raise AllocationError(
                    "Address 0x%x is already occupied" % (tmp * self.cellSize))
            if initValues is None:
                d[tmp] = 0
            else:
                d[tmp] = initValues[i]

        self.prevAllocatedAddrEnd = (indx + wordCnt) * self.cellSize
        return addr

    def getArray(self, addr: int, item_size: int, item_cnt: int):
        """
        Get array stored in memory
        """
        baseIndex = addr // self.cellSize
        if item_size != self.cellSize or baseIndex * self.cellSize != addr:
            return self._getArray(addr * 8, TransTmpl(Bits(item_size * 8)[item_cnt]))
        else:
            out = []
            for i in range(baseIndex, baseIndex + item_cnt):
                try:
                    v = self.data[i]
                except KeyError:
                    v = None

                out.append(v)
        return out

    def getBits(self, start, end, sign):
        """
        Gets value of bits between selected range from memory

        :param start: bit address of start of bit of bits
        :param end: bit address of first bit behind bits
        :return: instance of BitsVal (derived from SimBits type)
                 which contains copy of selected bits
        """
        wordWidth = self.cellSize * 8

        inFieldOffset = 0
        allMask = mask(wordWidth)
        value = Bits(end - start, signed=sign).from_py(None)

        while start != end:
            assert start < end, (start, end)

            dataWordIndex = start // wordWidth
            v = self.data.get(dataWordIndex, None)

            endOfWord = (dataWordIndex + 1) * wordWidth
            width = min(end, endOfWord) - start
            offset = start % wordWidth
            if v is None:
                val = 0
                vld_mask = 0
            elif isinstance(v, int):
                val = get_bit_range(v, offset, width)
                vld_mask = allMask
            else:
                val = get_bit_range(v.val, offset, width)
                vld_mask = get_bit_range(v.vld_mask, offset, width)

            m = mask(width)
            value.val |= (val & m) << inFieldOffset
            value.vld_mask |= (vld_mask & m) << inFieldOffset

            inFieldOffset += width
            start += width

        return value

    def _getArray(self, offset, transTmpl):
        """
        :param offset: global offset of this transTmpl (and struct)
        :param transTmpl: instance of TransTmpl which specifies items in array
        """
        t = transTmpl.dtype
        c = transTmpl.children
        arr_offset = offset
        item_width = c.bitAddrEnd - c.bitAddr
        value = []
        if not isinstance(t.element_t, Bits):
            raise NotImplementedError(t.element_t)

        for _ in range(t.size):
            v = self.getBits(arr_offset, arr_offset + item_width, None)
            value.append(v)
            arr_offset += item_width
        return value

    def _getStruct(self, offset, transTmpl):
        """
        :param offset: global offset of this transTmpl (and struct)
        :param transTmpl: instance of TransTmpl which specifies items in struct
        """
        dataDict = {}
        for subTmpl in transTmpl.children:
            t = subTmpl.dtype
            name = subTmpl.origin[-1].name
            if isinstance(t, Bits):
                value = self.getBits(
                    subTmpl.bitAddr + offset, subTmpl.bitAddrEnd + offset, t.signed)
            elif isinstance(t, HArray):
                value = self._getArray(subTmpl.bitAddr + offset, subTmpl)

            elif isinstance(t, HStruct):
                value = self._getStruct(offset, subTmpl)
            else:
                raise NotImplementedError(t)

            dataDict[name] = value

        return transTmpl.dtype.from_py(dataDict)

    def getStruct(self, addr, structT, bitAddr=None):
        """
        Get HStruct from memory

        :param addr: address where get struct from
        :param structT: instance of HStruct or FrameTmpl generated
                        from it to resolve structure of data
        :param bitAddr: optional bit precise address is is not None
                        param addr has to be None
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
