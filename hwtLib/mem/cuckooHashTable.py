from hwt.code import log2ceil
from hwt.interfaces.std import VectSignal
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.param import Param
from hwtLib.mem.hashTableCore import HashTableCore
from hwtLib.mem.hashTable_intf import LookupKeyIntf, InsertIntf, \
    LookupResultIntf


class CInsertIntf(InsertIntf):
    def _config(self):
        super(CInsertIntf, self)._config()
        self.TABLE_CNT = Param(2)

    def _declr(self):
        super(CInsertIntf, self)._declr()
        self.table = VectSignal(log2ceil(self.TABLE_CNT))

class CLookupResultIntf(LookupResultIntf):
    def _config(self):
        super(CLookupResultIntf, self)._config()
        self.TABLE_CNT = Param(2)

    def _declr(self):
        super(CLookupResultIntf, self)._config()
        self.table = VectSignal(self.TABLE_CNT)


# https://web.stanford.edu/class/cs166/lectures/13/Small13.pdf
class CuckooHashTableCore(HashTableCore):
    """
    Cuckoo hash uses more tables with different hash functions
    This is just simple container of these tables
    [TODO] only prototype yet
    """

    def __init__(self, polynomials):
        """
        :param polynomials: list of polynomials for crc hashers used in tables 
        """
        super(HashTableCore, self).__init__()
        self.POLYNOMIALS = polynomials

    def _config(self):
        self.TABLE_SIZE = Param(32)
        self.DATA_WIDTH = Param(32)
        self.KEY_WIDTH = Param(8)

    def _declr(self):
        addClkRstn(self)
        self.TABLE_CNT = len(self.POLYNOMIALS)
        self.HASH_WITH = log2ceil(self.TABLE_SIZE).val

        with self._paramsShared():
            self.insert = CInsertIntf()
            self.insert.HASH_WIDTH.set(self.HASH_WITH)

            self.lookup = LookupKeyIntf()

            self.lookupRes = CLookupResultIntf()
            self.lookupRes.HASH_WIDTH.set(self.HASH_WITH)
            self.lookupRes.TABLE_CNT.set(self.TABLE_CNT)


        self.table = [HashTableCore(p) for p  in self.POLYNOMIALS]
        with self._paramsShared():
            self._registerArray("table", self.table)
            for t in self.table:
                t.ITEMS_CNT.set(self.TABLE_SIZE)

    def _impl(self):
        propagateClkRstn(self)
        raise NotImplementedError()


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.logic.crcPoly import CRC_32
    u = CuckooHashTableCore([CRC_32, CRC_32])
    print(toRtl(u))
