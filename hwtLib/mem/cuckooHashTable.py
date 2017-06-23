from hwt.code import log2ceil
from hwt.interfaces.std import Handshaked, VectSignal, Signal
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.mem.ram import RamSingleClock
from hwtLib.mem.hashTable_intf import LookupKeyIntf


CHT_FOUND = 1


class CInsertPort(Handshaked):
    def _config(self):
        Handshaked._config(self)
        self.HASH_WIDTH = Param(8)

    def _declr(self):
        super(Handshaked, self)._declr()
        self.hash = VectSignal(self.HASH_WIDTH)
        self.table = VectSignal(1)


class CLookupResultIntf(Handshaked):
    def _config(self):
        Handshaked._config(self)
        self.HASH_WIDTH = Param(8)
        self.TABLE_CNT = Param(2)

    def _declr(self):
        Handshaked._declr(self)
        self.hash = VectSignal(self.HASH_WIDTH)
        self.table = VectSignal(self.TABLE_CNT)
        self.found = Signal()


# https://web.stanford.edu/class/cs166/lectures/13/Small13.pdf
class CuckooHashTableCore(Unit):
    """
    [TODO] not finished yet
    """
    def __init__(self, polynoms):
        super(CuckooHashTableCore, self).__init__()
        self.POLYNOMS = polynoms

    def _config(self):
        self.TABLE_CNT = Param(2)
        self.TABLE_SIZE = Param(1024)
        self.DATA_WIDTH = Param(32)
        self.KEY_WIDTH = Param(8)

    def _declr(self):
        self.HASH_WITH = log2ceil(self.TABLE_SIZE).val
        TABLE_CNT = int(self.TABLE_CNT)
        with self._paramsShared():
            self.insert = CInsertPort()
            self.insert.HASH_WIDTH.set(self.HASH_WITH)

            self.lookup = LookupKeyIntf()
            self.lookup.KEY_WIDTH.set(self.KEY_WITH)

            self.lookupRes = CLookupResultIntf()
            self.lookupRes.HASH_WIDTH.set(self.HASH_WITH)
            self.lookupRes.TABLE_CNT.set(self.TABLE_CNT)
        self.insertAck = Handshaked()
        self.insertAck.DATA_WIDTH.set(1)

        self.table = [RamSingleClock() for _ in range(TABLE_CNT)]
        with self._paramsShared():
            self._registerArray("table", self.table)
            for t in self.table:
                t.ITEMS_CNT.set(self.TABLE_SIZE)

    def _impl(self):
        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = CuckooHashTableCore()
    print(toRtl(u))