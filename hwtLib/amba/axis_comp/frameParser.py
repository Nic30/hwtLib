from hwt.code import log2ceil, If, Concat, And
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.std import Handshaked, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.byteOrder import reverseByteOrder
from hwt.synthesizer.param import Param
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.templateBasedUnit import TemplateBasedUnit


class AxiS_frameParser(AxiSCompBase, TemplateBasedUnit):
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

    :note: names in the picture are just illustrative
    """
    def __init__(self, axiSCls, structT, tmpl=None, frames=None):
        """
        :param axiSCls: class of input axi stream interface
        :param structT: instance of HStruct which specifies data format to download
        :param tmpl: instance of TransTmpl for this structT
        :param frames: list of FrameTemplate instances for this tmpl
        :note: if tmpl and frames are None they are resolved from structT parseTemplate
        :note: this unit can parse sequence of frames, if they are specified by "frames"
        :attention: structT can not contain fields with variable size like HStream
        """
        assert isinstance(structT, HStruct)
        self._structT = structT

        if tmpl is not None:
            assert frames is not None, "tmpl and frames can be used only together"
        else:
            assert frames is None, "tmpl and frames can be used only together"

        self._tmpl = tmpl
        self._frames = frames
        AxiSCompBase.__init__(self, axiSCls)

    def _config(self):
        self.intfCls._config(self)
        # if this is true field interfaces will be of type VldSynced
        # and single ready signal will be used for all
        # else every interface will be instance of Handshaked and it will
        # have it's own ready(rd) signal
        self.SHARED_READY = Param(False)
        # synchronize by last from input axi stream
        # or use internal counter for synchronization
        self.SYNCHRONIZE_BY_LAST = Param(True)

    def createInterfaceForField(self, structIntf, transInfo):
        if self.SHARED_READY:
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
            self.dataIn = self.intfCls()
            if self.SHARED_READY:
                self.dataOut_ready = Signal()

    def connectDataSignals(self, words, wordIndex):
        busVld = self.dataIn.valid
        if self.IS_BIGENDIAN:
            byteOrderCare = reverseByteOrder
        else:
            def byteOrderCare(sig):
                return sig
        signalsOfParts = []

        for wIndx, transParts, _ in words:
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
                    intf.data ** byteOrderCare(
                                               Concat(
                                                      *reversed(signalsOfParts)
                                                     )
                                              )
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

    def busReadyLogic(self, words, wordIndex):
        if self.SHARED_READY:
            busRd = self.ready
        else:
            # generate ready logic for struct fields
            _busRd = None
            for i, parts, _ in words:
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

    def _impl(self):
        r = self.dataIn
        self.parseTemplate()
        words = list(self.chainFrameWords())
        assert not (self.SYNCHRONIZE_BY_LAST and len(self._frames) > 1)
        maxWordIndex = words[-1][0]
        wordIndex = self._reg("wordIndex", vecT(log2ceil(maxWordIndex + 1)), 0)
        busVld = r.valid

        self.connectDataSignals(words, wordIndex)
        busRd = self.busReadyLogic(words, wordIndex)

        r.ready ** busRd

        if self.SYNCHRONIZE_BY_LAST:
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
