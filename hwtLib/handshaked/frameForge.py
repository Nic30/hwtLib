from hwt.interfaces.std import Handshaked
from hwt.synthesizer.interfaceLevel.mainBases import InterfaceBase
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.param import evalParam
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.code import log2ceil, Switch, If
from hwtLib.handshaked.streamNode import streamSync, streamAck
from hwt.interfaces.utils import addClkRstn
from hwt.bitmask import mask


class FrameTemplateItem(object):
    def __init__(self, name, typ, inFrameBitOffset, internalInterface, externalInterface):
        self.name = name
        self.type = typ

        self.inFrameBitOffset = inFrameBitOffset
        # list of tuples (word index, inWordBitUpper, inWordBitLower)
        self.appearsInWords = []

        self.internalInterface = internalInterface
        self.externalInterface = externalInterface


def formatIntoWords(frameInfos):
    wordRecord = []
    actualWord = 0
    for fi in frameInfos:
        for w, _, _ in fi.appearsInWords:
            if w == actualWord:
                wordRecord.append(fi)
            elif w > actualWord:
                yield actualWord, wordRecord
                wordRecord = [fi, ]
                actualWord = w
            else:
                raise NotImplementedError()

    if wordRecord:
        yield actualWord, wordRecord

class AxiSFrameForge(AxiSCompBase):
    """
    Assemble fields into frame on axi stream interface
    """
    def __init__(self, axiSIntfCls, frameTemplate):
        """
        @param hsIntfCls: class of interface which should be used as interface of this unit
        @param frameTemplate: iterable of info about fields in frame following formats are supported:
        tuple (type, name) or interface or signal
        if name is None no input port is generated and space is filled with invalid values
        litle-endian encoding,
        supported types of interfaces are: Handshaked, Signal
        """
        if axiSIntfCls is not AxiStream:
            raise NotImplementedError()

        self._frameTemplate = []
        inFrameOffset = 0
        for rec in frameTemplate:
            if isinstance(rec, (tuple, list)):
                typ, name = rec
                externalInterface = None
            elif isinstance(rec, (InterfaceBase, RtlSignalBase)):
                name = getSignalName(rec)
                typ = rec._dtype
                externalInterface = rec
            else:
                raise NotImplementedError("Unsupported field format", rec)
            fi = FrameTemplateItem(name, typ, inFrameOffset, None, externalInterface)
            self._frameTemplate.append(fi)
            inFrameOffset += typ.bit_length()

        assert len(self._frameTemplate) > 0
        AxiSCompBase.__init__(self, axiSIntfCls)

    def _declr(self):
        addClkRstn(self)
        self.dataOut = self.intfCls()
        for item in self._frameTemplate:
            if item.name is not None:
                ep = item.externalInterface
                if ep is not None:
                    p = ep.__class__()
                    setattr(self, item.name, p)
                    p._shareParamsWith(ep)
                else:
                    p = Handshaked()
                    p.DATA_WIDTH.set(item.type.bit_length())
                    setattr(self, item.name, p)
                item.internalInterface = p

    def _resolveFieldPossitionsInFrame(self):
        """
        @return: index of last word
        """
        DW = evalParam(self.DATA_WIDTH).val
        actualWord = 0
        for item in self._frameTemplate:
            w = item.type.bit_length()
            lower = item.inFrameBitOffset % DW
            remInFirstWord = DW - (item.inFrameBitOffset % DW)
            # align start
            if w <= remInFirstWord:
                upper = lower + w
                w = 0
            item.appearsInWords.append((actualWord, upper, lower))
            if w == 0:
                continue

            if w // DW > 0:
                # take aligned middle of field
                for _ in range(w // DW):
                    item.appearsInWords.append(
                                                (actualWord, DW, 0)
                                                )
                actualWord += w // DW

            if w != 0:
                # take reminder at the end
                item.appearsInWords.append(
                                            (actualWord, w, 0)
                                            )

        return actualWord

    def _impl(self):
        maxWordIndex = self._resolveFieldPossitionsInFrame()
        wordCntr = self._reg("wordCntr", vecT(log2ceil(maxWordIndex), False), defVal=0)
        dout = self.dataOut

        wcntrSw = Switch(wordCntr)
        for i, recs in formatIntoWords(self._frameTemplate):
            inPorts = []
            wordData = self._sig("word%d" % i, dout.data._dtype)

            for fi in recs:
                assert fi.appearsInWords
                for w, high, low in fi.appearsInWords:
                    if w == i:
                        if fi.internalInterface is None:
                            wordData[high:low] ** None
                        else:
                            wordData[high:low] ** fi.internalInterface.data
                            inPorts.append(fi.internalInterface)
            if inPorts:
                assignments = streamSync(masters=inPorts, slaves=[dout])
            else:
                assignments = []

            ack = streamAck(masters=inPorts, slaves=[dout])

            if i == maxWordIndex - 1:
                v = 0
            else:
                v = wordCntr + 1
            assignments.extend(If(ack,
                                  wordCntr ** v
                                  ))
            assignments.extend(dout.data ** wordData)
            print(wcntrSw, i, assignments)
            wcntrSw = wcntrSw.Case(i, assignments)

        default = dout.valid ** 1
        for fi in self._frameTemplate:
            if fi.internalInterface is not None:
                default.extend(fi.internalInterface.rd ** 0)
        wcntrSw.Default(default)

        dout.last ** wordCntr._eq(maxWordIndex - 1)
        dout.strb ** mask(8)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.types.ctypes import uint64_t, uint8_t, uint16_t
    u = AxiSFrameForge(AxiStream,
                       # tuples (type, name) where type has to be instance of Bits type
                       [(uint64_t, "item0"),
                        (uint64_t, None),  # name = None means this field will be ignored
                        (uint64_t, "item1"),
                        (uint8_t, "item2"), (uint8_t, "item3"), (uint16_t, "item4")
                        ])

    print(toRtl(u))
