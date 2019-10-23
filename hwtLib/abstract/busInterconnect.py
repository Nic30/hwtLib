from hwt.code import log2ceil, isPow2
from hwt.hdl.constants import READ, WRITE
from hwt.synthesizer.unit import Unit
from typing import List, Tuple, Set, Union


class AUTO_ADDR():
    """constant which means that address should be picked automatically"""
    pass


"""
:note: ACCESS_* belongs into feature set in master/slave specification
:var ACCESS_R: constant which specifies access to read only
:var ACCESS_W: constant which specifies access to write only
:var ACCESS_RW: constant which specifies access to read and write
"""
ACCESS_R = {READ}
ACCESS_W = {WRITE}
ACCESS_RW = {READ, WRITE}


class BusInterconnect(Unit):
    """
    Abstract class of bus interconnects

    :ivar m: HObjList of master interfaces
    :ivar s: HObjList of slave interfaces
    """

    def __init__(self,
                 masters: List[Tuple[int, Set]],
                 slaves: List[Tuple[Union[int, AUTO_ADDR], int, Set]]):
        """
        :param masters: list of tuples (offset, features) for each master
        :param slaves: list of tuples (offset, size, features) for each slave
        :note: features can be found on definition of this class
        """
        self._masters = masters

        _slaves = []
        maxAddr = 0
        for offset, size, features in slaves:
            if not isPow2(size):
                raise AssertionError(
                    "Size which is not power of 2 is suboptimal for interconnects")
            if offset == AUTO_ADDR:
                offset = maxAddr
                isAligned = (offset % size) == 0
                if not isAligned:
                    offset = ((offset // size) + 1) * size
            else:
                isAligned = (offset % size) == 0
                if not isAligned:
                    raise AssertionError("Offset which is not aligned to size is suboptimal")

            maxAddr = max(maxAddr, offset + size)
            _slaves.append((offset, size, features))

        self._slaves = sorted(_slaves, key=lambda x: x[0])

        # check for address space colisions
        lastAddr = -1
        for offset, size, features in self._slaves:
            if lastAddr >= offset:
                raise ValueError(
                    "Address space on address 0x%X colliding with previous" % offset)
            lastAddr = offset + size - 1

        super(BusInterconnect, self).__init__()

    def getOptimalAddrSize(self):
        assert self._slaves
        last = self._slaves[-1]
        maxAddr = last[0] + last[1]
        maxAddr -= self.DATA_WIDTH // 8
        assert maxAddr >= 0
        return log2ceil(maxAddr)
