#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Union

from hwt.code import log2ceil, If, Concat
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.frameTmplUtils import ChoicesOfFrameParts
from hwt.hdl.transPart import TransPart
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.hdl.types.union import HUnion
from hwt.interfaces.std import Handshaked, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSource, UnionSink
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.byteOrder import reverseByteOrder
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.frameParser_utils import ListOfOutNodeInfos, \
    ExclusieveListOfHsNodes, InNodeInfo, InNodeReadOnlyInfo, OutNodeInfo, \
    WordFactory
from hwtLib.amba.axis_comp.templateBasedUnit import TemplateBasedUnit
from hwtLib.handshaked.builder import HsBuilder


class AxiS_frameParser(AxiSCompBase, TemplateBasedUnit):
    """
    Parse frame specified by HType (HStruct, HUnion, ...) into fields
    
    :note: if special frame format is required,
        it can be specified by TransTmpl instance and list of FrameTmpl
        (Output data structure can be splited into multiple frames as required)

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

    .. hwt-schematic:: _example_AxiS_frameParser
    """

    def __init__(self, structT: HdlType,
                 tmpl: Optional[TransTmpl]=None,
                 frames: Optional[List[FrameTmpl]]=None):
        """
        :param structT: instance of HStruct which specifies data format to download
        :param tmpl: instance of TransTmpl for this structT
        :param frames: list of FrameTmpl instances for this tmpl
        :note: if tmpl and frames are None they are resolved from structT parseTemplate
        :note: this unit can parse sequence of frames, if they are specified by "frames"
        :attention: structT can not contain fields with variable size like HStream
        """
        self._structT = structT

        if tmpl is not None:
            assert frames is not None, "tmpl and frames can be used only together"
        else:
            assert frames is None, "tmpl and frames can be used only together"

        self._tmpl = tmpl
        self._frames = frames
        AxiSCompBase.__init__(self)

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

    def _mkFieldIntf(self, parent: Union[StructIntf, UnionSource],
                     structField: HStructField):
        t = structField.dtype
        if isinstance(t, HUnion):
            return UnionSource(t, parent._instantiateFieldFn)
        elif isinstance(t, HStruct):
            return StructIntf(t, parent._instantiateFieldFn)
        else:
            if self.SHARED_READY:
                i = VldSynced()
            else:
                i = Handshaked()
            i.DATA_WIDTH = structField.dtype.bit_length()
            return i

    def _declr(self):
        if self.USE_STRB:
            raise NotImplementedError(self.USE_STRB)
        if self.USE_KEEP:
            raise NotImplementedError(self.USE_KEEP)
        if self.ID_WIDTH:
            raise NotImplementedError(self.ID_WIDTH)
        if self.DEST_WIDTH:
            raise NotImplementedError(self.DEST_WIDTH)

        addClkRstn(self)

        if isinstance(self._structT, HStruct):
            intfCls = StructIntf
        elif isinstance(self._structT, HUnion):
            intfCls = UnionSource
        else:
            raise TypeError(self._structT)

        self.dataOut = intfCls(self._structT, self._mkFieldIntf)._m()

        with self._paramsShared():
            self.dataIn = self.intfCls()
            if self.SHARED_READY:
                self.dataOut_ready = Signal()

    def getInDataSignal(self, transPart: TransPart):
        busDataSignal = self.dataIn.data
        high, low = transPart.getBusWordBitRange()
        return busDataSignal[high:low]

    def choiceIsSelected(self, interfaceOfChoice: Union[UnionSource, UnionSink]):
        """
        Check if union member is selected by _select interface in union interface
        """
        parent = interfaceOfChoice._parent
        r = self._tmpRegsForSelect[parent]
        i = parent._interfaces.index(interfaceOfChoice)
        return i, r.data._eq(i), r.vld

    def connectParts(self,
                     allOutNodes: ListOfOutNodeInfos,
                     words,
                     wordIndexReg: Optional[RtlSignal]):
        """
        Create main datamux from dataIn to dataOut
        """
        for wIndx, transParts, _ in words:
            # each word index is used and there may be TransParts which are
            # representation of padding
            outNondes = ListOfOutNodeInfos()
            if wordIndexReg is None:
                isThisWord = hBit(1)
            else:
                isThisWord = wordIndexReg._eq(wIndx)

            for part in transParts:
                self.connectPart(outNondes, part, isThisWord, hBit(1))

            allOutNodes.addWord(wIndx, outNondes)

    def connectPart(self,
                    hsNondes: list,
                    part: Union[TransPart, ChoicesOfFrameParts],
                    en: Union[RtlSignal, bool],
                    exclusiveEn: Optional[RtlSignal]=hBit(1)):
        """
        Create datamux for one word in main fsm
        and colect metainformations for handshake logic

        :param hsNondes: list of nodes of handshaked logic
        """
        busVld = self.dataIn.valid
        tToIntf = self.dataOut._fieldsToInterfaces

        if isinstance(part, ChoicesOfFrameParts):
            parentIntf = tToIntf[part.origin.parent.origin]
            try:
                sel = self._tmpRegsForSelect[parentIntf]
            except KeyError:
                sel = HsBuilder(self, parentIntf._select).buff().end
                self._tmpRegsForSelect[parentIntf] = sel
            unionGroup = ExclusieveListOfHsNodes(sel)

            # for unions
            for choice in part:
                # connect data signals of choices and collect info about
                # streams
                intfOfChoice = tToIntf[choice.tmpl.origin]
                selIndex, isSelected, isSelectValid = self.choiceIsSelected(
                    intfOfChoice)
                _exclusiveEn = isSelectValid & isSelected & exclusiveEn

                unionMemberPart = ListOfOutNodeInfos()
                for p in choice:
                    self.connectPart(unionMemberPart, p, en, _exclusiveEn)
                unionGroup.append(selIndex, unionMemberPart)

            hsNondes.append(unionGroup)

            if part.isLastPart():
                # synchronization of reading from _select register for unions
                selNode = InNodeInfo(sel, en)
            else:
                selNode = InNodeReadOnlyInfo(sel, en)
            hsNondes.append(selNode)
            return

        if part.isPadding:
            return

        fPartSig = self.getInDataSignal(part)
        fieldInfo = part.tmpl.origin

        try:
            signalsOfParts = self._signalsOfParts[part.tmpl]
        except KeyError:
            signalsOfParts = []
            self._signalsOfParts[part.tmpl] = signalsOfParts

        if part.isLastPart():
            # connect all parts in this group to output stream
            signalsOfParts.append(fPartSig)
            intf = self.dataOut._fieldsToInterfaces[fieldInfo]
            intf.data(self.byteOrderCare(
                Concat(
                    *reversed(signalsOfParts)
                ))
            )
            on = OutNodeInfo(self, intf, en, exclusiveEn)
            hsNondes.append(on)
        else:
            dataVld = busVld & en & exclusiveEn
            # part is in some word as last part, we have to store its value to register
            # until the last part arrive
            fPartReg = self._reg("%s_part_%d" % (fieldInfo.name,
                                                 len(signalsOfParts)),
                                 fPartSig._dtype)
            If(dataVld,
               fPartReg(fPartSig)
            )
            signalsOfParts.append(fPartReg)

    def _impl(self):
        r = self.dataIn
        self.parseTemplate()
        words = list(self.chainFrameWords())
        assert not (self.SYNCHRONIZE_BY_LAST and len(self._frames) > 1)
        maxWordIndex = words[-1][0]
        hasMultipleWords = maxWordIndex > 0
        if hasMultipleWords:
            wordIndex = self._reg("wordIndex", Bits(
                log2ceil(maxWordIndex + 1)), 0)
        else:
            wordIndex = None

        busVld = r.valid

        if self.IS_BIGENDIAN:
            byteOrderCare = reverseByteOrder
        else:
            def byteOrderCare(sig):
                return sig

        self.byteOrderCare = byteOrderCare
        self._tmpRegsForSelect = {}
        self._signalsOfParts = {}

        allOutNodes = WordFactory(wordIndex)
        self.connectParts(allOutNodes, words, wordIndex)

        if self.SHARED_READY:
            busReady = self.dataOut_ready
            r.ready(busReady)
        else:
            busReady = self._sig("busReady")
            busReady(allOutNodes.ack())
            allOutNodes.sync(busVld)

        r.ready(busReady)

        if hasMultipleWords:
            if self.SYNCHRONIZE_BY_LAST:
                last = r.last
            else:
                last = wordIndex._eq(maxWordIndex)

            If(busVld & busReady,
                If(last,
                   wordIndex(0)
                   ).Else(
                    wordIndex(wordIndex + 1)
                )
               )


def _example_AxiS_frameParser():
    from hwtLib.types.ctypes import uint32_t, uint64_t
    # t = HStruct(
    #  (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
    #  (uint64_t, None),  # name = None means this field will be ignored
    #  (uint64_t, "item1"),
    #  (uint64_t, None),
    #  (uint16_t, "item2"),
    #  (uint16_t, "item3"),
    #  (uint32_t, "item4"),
    #  (uint32_t, None),
    #  (uint64_t, "item5"),  # this word is split on two bus words
    #  (uint32_t, None),
    #  (uint64_t, None),
    #  (uint64_t, None),
    #  (uint64_t, None),
    #  (uint64_t, "item6"),
    #  (uint64_t, "item7"),
    #  (HStruct(
    #      (uint64_t, "item0"),
    #      (uint64_t, "item1"),
    #   ),
    #   "struct0")
    #  )
    # t = HUnion(
    #    (uint32_t, "a"),
    #    (int32_t, "b")
    #    )

    t = HUnion(
        (HStruct(
            (uint64_t, "itemA0"),
            (uint64_t, "itemA1")
        ), "frameA"),
        (HStruct(
            (uint32_t, "itemB0"),
            (uint32_t, "itemB1"),
            (uint32_t, "itemB2"),
            (uint32_t, "itemB3")
        ), "frameB")
    )
    u = AxiS_frameParser(t)
    u.DATA_WIDTH = 64
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl

    u = _example_AxiS_frameParser()

    print(
        toRtl(u)
    )
