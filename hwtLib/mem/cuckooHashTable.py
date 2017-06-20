from hwt.code import log2ceil, If, connect
from hwt.interfaces.std import Handshaked, VectSignal, Signal, HandshakeSync
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.logic.crcComb import CrcComb
from hwtLib.mem.ram import RamSingleClock


CHT_FOUND = 1


class CInsertPort(Handshaked):
    def _config(self):
        Handshaked._config(self)
        self.HASH_WIDTH = Param(8)

    def _declr(self):
        super(Handshaked, self)._declr()
        self.hash = VectSignal(self.HASH_WIDTH)
        self.table = VectSignal(1)


class CLoockupKeyIntf(HandshakeSync):
    def _config(self):
        self.KEY_WIDTH = Param(8)

    def _declr(self):
        HandshakeSync._declr(self)
        self.key = VectSignal(self.KEY_WIDTH)


class CLoockupResultIntf(Handshaked):
    def _config(self):
        Handshaked._config(self)
        self.HASH_WIDTH = Param(8)
        self.TABLE_CNT = Param(1)

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
        TABLE_CNT = evalParam(self.TABLE_CNT).val
        with self._paramsShared():
            self.insert = CInsertPort()
            self.insert.HASH_WIDTH.set(self.HASH_WITH)

            self.lookup = CLoockupKeyIntf()
            self.lookup.KEY_WIDTH.set(self.KEY_WITH)

            self.lookupRes = CLoockupResultIntf()
            self.lookupRes.HASH_WIDTH.set(self.HASH_WITH)
            self.lookupRes.TABLE_CNT.set(self.TABLE_CNT)
        self.insertAck = Handshaked()
        self.insertAck.DATA_WIDTH.set(1)

        self.table = [RamSingleClock() for _ in range(TABLE_CNT)]
        for t in self.table:
            t.PORT_CNT.set(1)
            t.ADDR_WIDTH.set(log2ceil(self.TABLE_SIZE))
            t.DATA_WIDTH.set(1 + self.KEY_WIDTH + self.DATA_WIDTH)  # +1 for vldFlag
        self._registerArray("table", self.table)

        self.hash = [CrcComb() for _ in range()]
        hashWidth = max(evalParam(self.KEY_WIDTH).val, self.HASH_WITH)
        assert len(self.POLYNOMS) == TABLE_CNT
        for h, poly in zip(self.hash, self.POLYNOMS):
            h.DATA_WIDTH.set(hashWidth)
            h.POLY.set(poly)
            h.POLY_WIDTH.set(hashWidth)

    def _impl(self):
        propagateClkRstn(self)
        tables = list(map(lambda r: r.a, self.tables))
        r = self._reg

        for h in self.hash:
            h.dataIn ** self.lookup.key

        lookupEn = r("lookupEn", defVal=1)
        lookupPendingReq = r("lookupPendingReq", defVal=0)
        lookupPendingAck = r("lookupPendingAck", defVal=0)
        lookupPending = lookupPendingReq != lookupPendingAck

        self.lookup.rd ** lookupEn
        for t, h in zip(tables, self.hash):
            t.din ** self.insert.data
            t.we ** ~lookupEn

            If(lookupEn,
               If(self.lookup.vld,
                  lookupPendingReq ** ~lookupPendingReq
               ),
               connect(h.dataOut, t.addr, fit=True),
               t.en ** self.lookup.vld,
            ).Else(
               connect(self.insert.hash, t.addr, fit=True),
               t.en ** self.insert.vld
            )

            If(lookupPending,
               lookupPendingAck ** ~lookupPendingAck
            )
            