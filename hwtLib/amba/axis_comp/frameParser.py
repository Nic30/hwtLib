from math import inf

from hwt.code import log2ceil, If, Concat, And
from hwt.hdlObjects.frameTemplate import FrameTemplate
from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.std import Handshaked, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam, Param


class AxiS_frameParser(Unit):
    """
    Parse frame specified by HStruct into fields

    .. aafig::
                                     +---------+
                              +------> field0  |
                              |      +---------+
                      +-------+-+
         input stream |         |    +---------+
        +-------------> parser  +----> field1  |
                      |         |    +---------+
                      +-------+-+
                              |      +---------+
                              +------> field2  |
                                     +---------+

    """
    def __init__(self, axiSCls, structT, maxPaddingWords=inf):
        """
        :param axiSCls: class of input axi stream interface
        :param structT: instance of HStruct which specifies data format to download
        :attention: structT can not contain fields with variable size like HStream
        """
        super(AxiS_frameParser, self).__init__()
        assert isinstance(structT, HStruct)
        self._structT = structT
        self._axiSCls = axiSCls
        self._maxPaddingWords = maxPaddingWords

    def _config(self):
        self.DATA_WIDTH = Param(64)
        # if this is true field interfaces will be of type VldSynced
        # and single ready signal will be used for all
        # else every interface will be instance of Handshaked and it will
        # have it's own ready(rd) signal
        self.SHARED_READY = Param(False)
        # synchronize by last from input axi stream
        # or use internal counter for synchronization
        self.SYNCHRONIZE_BY_LAST = Param(True)

    def createInterfaceForField(self, structIntf, transInfo):
        if evalParam(self.SHARED_READY).val:
            i = VldSynced()
        else:
            i = Handshaked()
        i.DATA_WIDTH.set(transInfo.dtype.bit_length())
        return i

    def getInDataSignal(self, transactionPart):
        busDataSignal = self.dataIn.data
        bitRange = transactionPart.getBusWordBitRange()
        return busDataSignal[bitRange[0]:bitRange[1]]

    def _declr(self):
        addClkRstn(self)
        self.dataOut = StructIntf(self._structT,
                                  self.createInterfaceForField)

        with self._paramsShared():
            self.dataIn = self._axiSCls()
            if evalParam(self.SHARED_READY).val:
                self.dataOut_ready = Signal()

    def connectDataSignals(self, words, wordIndex):
        busVld = self.dataIn.valid

        signalsOfParts = []

        for wIndx, transParts in words:
            isThisWord = wordIndex._eq(wIndx)

            for part in transParts:
                if part.isPadding:
                    continue
                dataVld = busVld & isThisWord
                fPartSig = self.getInDataSignal(part)
                fieldInfo = part.tmpl.origin

                if part.isLastPart():
                    signalsOfParts.append(fPartSig)
                    intf = self.dataOut._fieldsToInterfaces[fieldInfo]
                    intf.data ** Concat(*reversed(signalsOfParts))
                    intf.vld ** dataVld
                    signalsOfParts = []
                else:
                    # part is in some word as last part, we have to store its value to register
                    # until the last part arrive
                    fPartReg = self._reg("%s_part_%d" % (fieldInfo.name, len(signalsOfParts)), fPartSig._dtype)
                    If(dataVld,
                       fPartReg ** fPartSig
                    )
                    signalsOfParts.append(fPartReg)

    def busReadyLogic(self, words, wordIndex, maxWordIndex):
        if evalParam(self.SHARED_READY).val:
            busRd = self.ready
        else:
            # generate ready logic for struct fields
            _busRd = None
            for i, parts in words:
                lastParts = where(parts, lambda p: not p.isPadding and p.isLastPart())
                fiedsRd = map(lambda p: self.dataOut._fieldsToInterfaces[p.tmpl.origin].rd,
                              lastParts)
                isThisIndex = wordIndex._eq(i)
                if _busRd is None:
                    _busRd = And(isThisIndex, *fiedsRd)
                else:
                    _busRd = _busRd | And(isThisIndex, *fiedsRd)

            busRd = self._sig("busAck")
            busRd ** _busRd
        return busRd

    def parseTemplate(self):
        self._tmpl = TransTmpl(self._structT)
        DW = evalParam(self.DATA_WIDTH).val
        frames = FrameTemplate.framesFromTransTmpl(self._tmpl,
                                                             DW,
                                                             maxPaddingWords=self._maxPaddingWords)
        self._frames = list(frames)

    def _impl(self):
        r = self.dataIn
        self.parseTemplate()
        assert len(self._frames) == 1
        words = list(self._frames[0].walkWords(showPadding=True))

        maxWordIndex = words[-1][0]
        wordIndex = self._reg("wordIndex", vecT(log2ceil(maxWordIndex + 1)), 0)
        busVld = r.valid

        self.connectDataSignals(words, wordIndex)
        busRd = self.busReadyLogic(words, wordIndex, maxWordIndex)

        r.ready ** busRd

        if evalParam(self.SYNCHRONIZE_BY_LAST).val:
            last = r.last
        else:
            last = wordIndex._eq(maxWordIndex)

        If(busVld & busRd,
            If(last,
               wordIndex ** 0
            ).Else(
                wordIndex ** (wordIndex + 1)
            )
        )


if __name__ == "__main__":
    from hwtLib.types.ctypes import uint16_t, uint32_t, uint64_t
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.amba.axis import AxiStream

    s = HStruct(
        (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
        (uint64_t, None),  # name = None means this field will be ignored
        (uint64_t, "item1"),
        (uint64_t, None),
        (uint16_t, "item2"),
        (uint16_t, "item3"),
        (uint32_t, "item4"),

        (uint32_t, None),
        (uint64_t, "item5"),  # this word is split on two bus words
        (uint32_t, None),

        (uint64_t, None),
        (uint64_t, None),
        (uint64_t, None),
        (uint64_t, "item6"),
        (uint64_t, "item7"),
        (HStruct(
            (uint64_t, "item0"),
            (uint64_t, "item1"),
         ),
         "struct0")
        )
    u = AxiS_frameParser(AxiStream, s)
    u.DATA_WIDTH.set(51)
    print(toRtl(u))
