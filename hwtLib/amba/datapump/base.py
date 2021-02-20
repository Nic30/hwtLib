from typing import Union, List

from hwt.code import If, Switch
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import HandshakeSync
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil, isPow2
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import fitTo, fitTo_t
from hwtLib.amba.axi3 import Axi3_addr, Axi3
from hwtLib.amba.axi3Lite import Axi3Lite_addr
from hwtLib.amba.axi4 import Axi4, Axi4_addr
from hwtLib.amba.axi4Lite import Axi4Lite_addr
from hwtLib.amba.constants import BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, PROT_DEFAULT, QOS_DEFAULT, BYTES_IN_TRANS
from hwtLib.amba.datapump.intf import AddrSizeHs
from hwtLib.handshaked.streamNode import StreamNode
from pyMathBitPrecise.bit_utils import mask, align_with_known_width
from hwt.hdl.types.defs import BIT


class AxiDatapumpBase(Unit):
    """
    :ivar ~.MAX_TRANS_OVERLAP: max number of concurrent transactions
    :ivar ~.CHUNK_WIDTH: number of bits for one transaction chunk (a transaction is defined
        as a stream of chunks, if CHUNK_WIDTH==DATA_WIDTH it means that the transaction size % DATA_WIDTH == 0)
    :ivar ~.MAX_CHUNKS: maximum number of chunks in a transaction
    :ivar ~.ALIGNAS: specifies alignment requirement for a data type t (in bits),
        same functionailty as C++11 alignas specifier, used to discard alignment logic
    :ivar ~.driver: interface which is used to drive this datapump
        (AxiRDatapumpIntf or AxiWDatapumpIntf)
    """

    def __init__(self, axiCls=Axi4):
        self._axiCls = axiCls
        super().__init__()

    def _config(self):
        self.MAX_TRANS_OVERLAP = Param(16)
        self.ALIGNAS = Param(64 // 8)
        self.CHUNK_WIDTH = Param(64)
        self.MAX_CHUNKS = Param(4096 // self.CHUNK_WIDTH)

        self.ID_WIDTH = Param(4 if issubclass(self._axiCls, (Axi3, Axi4)) else 0)
        self.ADDR_WIDTH = Param(32)
        self.USER_WIDTH = Param(0)
        self.ADDR_USER_VAL = Param(None)

        self.DATA_WIDTH = Param(64)
        self.ID_VAL = Param(0)
        self.CACHE_VAL = Param(CACHE_DEFAULT)
        self.PROT_VAL = Param(PROT_DEFAULT)
        self.QOS_VAL = Param(QOS_DEFAULT)
        self.USE_STRB = Param(True)
        self.AXI_CLS = Param(self._axiCls)

    def _declr(self):
        addClkRstn(self)
        assert self.ALIGNAS % 8 == 0 and self.ALIGNAS > 0 and self.ALIGNAS <= self.DATA_WIDTH
        assert isPow2(self.ALIGNAS), self.ALIGNAS
        if self.MAX_CHUNKS != 1:
            assert self.CHUNK_WIDTH % 8 == 0, self.CHUNK_WIDTH
            assert isPow2(self.CHUNK_WIDTH)
        assert self.MAX_CHUNKS > 0, self.MAX_CHUNKS

        with self._paramsShared():
            # address channel to axi
            self.axi = self._axiCls()._m()

    def getSizeAlignBits(self):
        return log2ceil(self.DATA_WIDTH // 8)

    def addrAlign(self, addr: RtlSignal):
        return align_with_known_width(addr, addr._dtype.bit_length(), self.getSizeAlignBits())

    def addrIsAligned(self, addr: RtlSignal):
        return addr[self.getSizeAlignBits():]._eq(0)

    def isAlwaysAligned(self):
        return self.ALIGNAS == self.DATA_WIDTH

    def getShiftOptions(self):
        SHIFT_OPTIONS = []
        for x in range(self.DATA_WIDTH):
            sh = x * self.ALIGNAS
            if sh >= self.DATA_WIDTH:
                break
            SHIFT_OPTIONS.append(sh)
        return tuple(SHIFT_OPTIONS)

    def encodeShiftValue(self, SHIFT_OPTIONS: List[int], addrOffset: RtlSignal, shift: RtlSignal):
        assert not self.isAlwaysAligned()
        return Switch(addrOffset).add_cases(
                (sh // 8, shift(i))
                for i, sh in enumerate(SHIFT_OPTIONS)
            ).Default(
                shift(None),
            )

    def useTransSplitting(self):
        req_len_max = self.driver.req.MAX_LEN + 1
        axi_len_max = 2 ** self.axi.LEN_WIDTH
        if req_len_max > axi_len_max:
            return True

        elif req_len_max == axi_len_max:
            req_word_crosses_axi_word_boundary = (self.ALIGNAS != self.DATA_WIDTH) and (self.CHUNK_WIDTH >= self.DATA_WIDTH)
            for offset in range(0, self.DATA_WIDTH, self.ALIGNAS):
                if offset + self.CHUNK_WIDTH > self.DATA_WIDTH:
                    # if using any offset we cross bus word boundary
                    req_word_crosses_axi_word_boundary = True

            return req_word_crosses_axi_word_boundary
        else:
            return False

    def getBurstAddrOffset(self):
        return (self.getAxiLenMax() + 1) << self.getSizeAlignBits()

    def getAxiLenMax(self):
        return mask(self.axi.LEN_WIDTH)

    def axiAddrDefaults(self, a: Union[Axi3_addr, Axi3Lite_addr, Axi4_addr, Axi4Lite_addr]):
        if isinstance(a, (Axi3_addr, Axi4_addr)):
            a.burst(BURST_INCR)
            a.cache(self.CACHE_VAL)
            a.lock(LOCK_DEFAULT)
            a.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))
            if a.USER_WIDTH:
                a.user(self.ADDR_USER_VAL)

        if hasattr(a, "prot"):
            a.prot(self.PROT_VAL)
        if hasattr(a, "qos"):
            a.qos(self.QOS_VAL)

    def getLen_t(self):
        len_t = self.driver.req.len._dtype
        if not self.isAlwaysAligned():
            len_t = Bits(len_t.bit_length() + 1, signed=False)
        return len_t

    def hasAlignmentError(self, addr: RtlSignal):
        if self.ALIGNAS == 8:
            return BIT.from_py(0)
        else:
            return addr[log2ceil(self.CHUNK_WIDTH // 8):] != 0

    def isCrossingWordBoundary(self, addr, rem):
        offset_t = Bits(self.getSizeAlignBits() + 1, signed=False)
        word_B = offset_t.from_py(self.DATA_WIDTH // 8)
        bytesInLastWord = rem._eq(0)._ternary(word_B, fitTo_t(rem, offset_t))
        bytesAvaliableInLastWord = (word_B - fitTo_t(addr[self.getSizeAlignBits():], offset_t))
        crossesWordBoundary = rename_signal(self, bytesInLastWord > bytesAvaliableInLastWord, "crossesWordBoundary")
        return crossesWordBoundary

    def addrHandler(self,
                    req: AddrSizeHs,
                    axiA: Union[Axi3_addr, Axi3Lite_addr, Axi4_addr, Axi4Lite_addr],
                    transInfo: HandshakeSync, errFlag: RtlSignal):
        """
        Propagate read/write requests from req to axi address channel
        and store extra info using transInfo interface.
        """
        r, s = self._reg, self._sig

        self.axiAddrDefaults(axiA)
        if self.ID_WIDTH:
            axiA.id(self.ID_VAL)

        alignmentError = self.hasAlignmentError(req.addr)

        HAS_LEN = self._axiCls.LEN_WIDTH > 0
        if self.useTransSplitting():
            # if axi len is smaller we have to use transaction splitting
            # that means we need to split requests from driver.req to multiple axi requests
            transPartPending = r("transPartPending", def_val=0)
            addrTmp = r("addrTmp", req.addr._dtype)

            dispatchNode = StreamNode(
                [req, ],
                [axiA, transInfo],
                skipWhen={req: transPartPending.next},
                extraConds={
                    req:~transPartPending.next,
                    axiA: req.vld & ~alignmentError,
                    transInfo: req.vld & ~alignmentError
                }
            )
            dispatchNode.sync(~errFlag)
            ack = s("ar_ack")
            ack(dispatchNode.ack() & ~errFlag)

            LEN_MAX = max(mask(self._axiCls.LEN_WIDTH), 0)
            reqLen = s("reqLen", self.getLen_t())
            reqLenRemaining = r("reqLenRemaining", reqLen._dtype)

            If(reqLen > LEN_MAX,
               *([axiA.len(LEN_MAX)] if HAS_LEN else []),
               self.storeTransInfo(transInfo, 0)
            ).Else(
                # connect only lower bits of len
                * ([axiA.len(reqLen, fit=True)] if HAS_LEN else []),
                self.storeTransInfo(transInfo, 1)
            )

            # dispatchNode not used because of combinational loop
            If(StreamNode([req, ], [axiA, transInfo]).ack() & ~errFlag,
                If(reqLen > LEN_MAX,
                    reqLenRemaining(reqLen - (LEN_MAX + 1)),
                    transPartPending(1)
                ).Else(
                    transPartPending(0)
                )
            )
            reqLenSwitch = If(~req.vld,
                    reqLen(None),
            )
            if not self.isAlwaysAligned():
                crossesWordBoundary = self.isCrossingWordBoundary(req.addr, req.rem)
                reqLenSwitch.Elif(~self.addrIsAligned(req.addr) & crossesWordBoundary,
                    reqLen(fitTo(req.len, reqLen, shrink=False) + 1),
                )
            reqLenSwitch.Else(
                reqLen(fitTo(req.len, reqLen, shrink=False)),
            )

            ADDR_STEP = self.getBurstAddrOffset()
            If(transPartPending,
                axiA.addr(self.addrAlign(addrTmp)),
                If(ack,
                   addrTmp(addrTmp + ADDR_STEP)
                ),
                reqLen(reqLenRemaining),
            ).Else(
                axiA.addr(self.addrAlign(req.addr)),
                addrTmp(req.addr + ADDR_STEP),
                reqLenSwitch,
            )

        else:
            # if axi len is wider we can directly translate requests to axi
            axiA.addr(self.addrAlign(req.addr))
            if req.MAX_LEN > 0:
                lenDrive = axiA.len(fitTo(req.len, axiA.len, shrink=False))

                if not self.isAlwaysAligned():
                    crossesWordBoundary = self.isCrossingWordBoundary(req.addr, req.rem)
                    If(~self.addrIsAligned(req.addr) & crossesWordBoundary,
                       axiA.len(fitTo(req.len, axiA.len) + 1),
                    ).Else(
                       lenDrive,
                    )
            else:
                if HAS_LEN:
                    axiA.len(0)

            self.storeTransInfo(transInfo, 1)
            StreamNode(
                masters=[req],
                slaves=[axiA, transInfo],
                extraConds={
                    axiA:~alignmentError,
                    transInfo:~alignmentError,
                }
            ).sync(~errFlag)

