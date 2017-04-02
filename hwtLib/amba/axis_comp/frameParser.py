from math import inf

from hwt.code import log2ceil, If, Concat, And
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.types.structUtils import StructFieldInfo, \
    StructBusBurstInfo
from hwt.interfaces.std import Handshaked, Signal, VldSynced
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam, Param


class AxiS_frameParser(Unit):
    """
    Parse frame specified by HStruct into fields
    """
    def __init__(self, axiSCls, structT):
        """
        :param axiSCls: class of input axi stream interface
        :param structT: instance of HStruct which specifies data format to download
        :attention: interfaces for each field in struct will be dynamically created
        :attention: structT can not contain fields with variable size like HStream
        """
        super(AxiS_frameParser, self).__init__()
        assert isinstance(structT, HStruct)
        self._structT = structT
        self._axiSCls = axiSCls

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

    def _createInterfaceForField(self, fInfo):
        if evalParam(self.SHARED_READY).val:
            i = VldSynced()
        else:
            i = Handshaked()
        i.DATA_WIDTH.set(fInfo.type.bit_length())
        fInfo.interface = i
        return i

    def _declareFieldInterfaces(self):
        """
        Declare interfaces for struct fields and collect StructFieldInfo for each field
        """
        structInfo = []
        busDataWidth = evalParam(self.DATA_WIDTH).val
        startBitIndex = 0
        for f in self._structT.fields:
            name, t = f.name, f.type
            if name is not None:
                info = StructFieldInfo(t, name)
                startBitIndex = info.discoverFieldParts(busDataWidth, startBitIndex)
                i = self._createInterfaceForField(info)

                setattr(self, name, i)
                structInfo.append(info)
            else:
                startBitIndex += t.bit_length()

        return structInfo

    def _declr(self, declareInput=True, maxDummyWords=inf):
        addClkRstn(self)
        structInfo = self._declareFieldInterfaces()
        self._busBurstInfo = StructBusBurstInfo.packFieldInfosToBusBurst(
                                    structInfo,
                                    maxDummyWords,
                                    evalParam(self.DATA_WIDTH).val // 8)

        if declareInput:
            with self._paramsShared():
                self.dataIn = self._axiSCls()
                if evalParam(self.SHARED_READY).val:
                    self.ready = Signal()

    def _impl(self):
        r = self.dataIn
        maxWordIndex = StructBusBurstInfo.sumOfWords(self._busBurstInfo)
        wordIndex = self._reg("wordIndex", vecT(log2ceil(maxWordIndex + 1)), 0)
        busVld = r.valid

        for burstInfo in self._busBurstInfo:
            for fieldInfo in burstInfo.fieldInfos:
                lastPart = fieldInfo.parts[-1]
                signalsOfParts = []

                for i, part in enumerate(fieldInfo.parts):
                    dataVld = busVld & wordIndex._eq(part.wordIndex)
                    fPartSig = part.getSignal(r.data)

                    if part is lastPart:
                        signalsOfParts.append(fPartSig)
                        fieldInfo.interface.data ** Concat(*signalsOfParts)
                        fieldInfo.interface.vld ** dataVld

                    else:
                        if part.wordIndex < lastPart.wordIndex:
                            # part is in some word before last, we have to store its value to reg till the last part arrive
                            fPartReg = self._reg("%s_part_%d" % (fieldInfo.name, i), fPartSig._dtype)
                            If(dataVld,
                               fPartReg ** fPartSig
                            )
                            signalsOfParts.append(fPartReg)
                        else:
                            # part is in same word as last so we can take it directly
                            signalsOfParts.append(fPartSig)

        if evalParam(self.SHARED_READY).val:
            busRd = self.ready
        else:
            # generate ready logic for struct fields
            # dict index of word :  list of field parts
            endOfFieldsInWords = {}
            for burstInfo in self._busBurstInfo:
                for fieldInfo in burstInfo.fieldInfos:
                    lastPart = fieldInfo.parts[-1]
                    endOfFieldsInWords.setdefault(lastPart.wordIndex, [])\
                                      .append(fieldInfo)

            _busRd = None
            for i in range(maxWordIndex + 1):
                fields = endOfFieldsInWords.get(i, [])
                fiedsRd = map(lambda f: f.interface.rd,
                              fields)
                isThisIndex = wordIndex._eq(i)
                if _busRd is None:
                    _busRd = And(isThisIndex, *fiedsRd)
                else:
                    _busRd = _busRd | And(isThisIndex, *fiedsRd)

            busRd = self._sig("busAck")
            busRd ** _busRd
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
        )

    u = AxiS_frameParser(AxiStream, s)
    print(toRtl(u))
 
