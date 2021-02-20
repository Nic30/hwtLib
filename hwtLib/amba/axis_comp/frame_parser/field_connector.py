from typing import Union, Optional

from hwt.code import If, Switch, Concat
from hwt.hdl.frameTmplUtils import ChoicesOfFrameParts
from hwt.hdl.transPart import TransPart
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStructField
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSource, UnionSink
from hwt.synthesizer.byteOrder import reverseByteOrder
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.frame_parser.out_containers import ListOfOutNodeInfos, \
    ExclusieveListOfHsNodes, InNodeInfo, InNodeReadOnlyInfo, OutStreamNodeGroup, \
    OutStreamNodeInfo, OutNodeInfo
from hwtLib.handshaked.builder import HsBuilder
from pyMathBitPrecise.bit_utils import mask


def get_byte_order_modifier(axis: AxiStream):
    if axis.IS_BIGENDIAN:
        return reverseByteOrder
    else:

        def byteOrderCare(sig):
            return sig

        return byteOrderCare


class AxiS_frameParserFieldConnector():

    def __init__(self, parent: Unit, dataIn: AxiStream, dataOut: Union[StructIntf, UnionSource]):
        self.parent = parent
        self.dataIn = dataIn
        self.dataOut = dataOut
        self.byteOrderCare = get_byte_order_modifier(dataIn)
        self._tmpRegsForSelect = {}
        # TransTmpl: List[RtlSignal]
        self._signalsOfParts = {}
        # AxiStream: OutStreamNodeInfo
        self._streamNodes = {}

    def getInDataSignal(self, transPart: TransPart):
        busDataSignal = self.dataIn.data
        high, low = transPart.getBusWordBitRange()
        return busDataSignal[high:low]

    def choiceIsSelected(self,
                         interfaceOfChoice: Union[UnionSource, UnionSink]):
        """
        Check if union member is selected by _select interface
        in union interface
        """
        parent = interfaceOfChoice._parent
        r = self._tmpRegsForSelect[parent]
        i = parent._interfaces.index(interfaceOfChoice)
        return i, r.data._eq(i), r.vld

    def connectParts(self,
                     allOutNodes: ListOfOutNodeInfos,
                     words,
                     wordIndex: Optional[RtlSignal]):
        """
        Create main datamux from dataIn to dataOut
        """
        for currentWordIndex, transParts, _ in words:
            # each word index is used and there may be TransParts which are
            # representation of padding
            outNondes = ListOfOutNodeInfos()
            for part in transParts:
                self.connectPart(outNondes, part, BIT.from_py(1), BIT.from_py(1),
                                 wordIndex, currentWordIndex)

            allOutNodes.addWord(currentWordIndex, outNondes)

    def connectChoicesOfFrameParts(
            self,
            hsNondes: ListOfOutNodeInfos,
            part: ChoicesOfFrameParts,
            en: Union[RtlSignal, bool],
            exclusiveEn: Optional[RtlSignal],
            wordIndex: Optional[RtlSignal],
            currentWordIndex: int):
        tToIntf = self.dataOut._fieldsToInterfaces
        parentIntf = tToIntf[part.origin.parent.getFieldPath()]
        try:
            sel = self._tmpRegsForSelect[parentIntf]
        except KeyError:
            sel = HsBuilder(self.parent, parentIntf._select).buff().end
            self._tmpRegsForSelect[parentIntf] = sel
        unionGroup = ExclusieveListOfHsNodes(sel)

        # for unions
        for choice in part:
            # connect data signals of choices and collect info about
            # streams
            intfOfChoice = tToIntf[choice.tmpl.getFieldPath()]
            selIndex, isSelected, isSelectValid = self.choiceIsSelected(
                intfOfChoice)
            _exclusiveEn = isSelectValid & isSelected & exclusiveEn

            unionMemberPart = ListOfOutNodeInfos()
            for p in choice:
                self.connectPart(unionMemberPart, p, en, _exclusiveEn,
                                 wordIndex, currentWordIndex)
            unionGroup.append(selIndex, unionMemberPart)
        hsNondes.append(unionGroup)

        if wordIndex is not None:
            en = en & wordIndex._eq(currentWordIndex)
        if part.isLastPart():
            # synchronization of reading from _select register for unions
            selNode = InNodeInfo(sel, en)
        else:
            selNode = InNodeReadOnlyInfo(sel, en)
        hsNondes.append(selNode)

    def connectStreamOfFrameParts(
            self,
            hsNondes: ListOfOutNodeInfos,
            part: Union[TransPart, ChoicesOfFrameParts],
            en: Union[RtlSignal, bool],
            exclusiveEn: Optional[RtlSignal],
            wordIndex: Optional[RtlSignal],
            currentWordIndex: int):
        orig = part.tmpl.origin[-1]
        # use tmpl.parent because part is actually a chunk of data
        # in the stream
        path_to_stream_port = part.tmpl.parent.getFieldPath()
        dout = self.dataOut._fieldsToInterfaces[path_to_stream_port]
        if isinstance(orig, HStructField):
            orig = orig.dtype
        assert isinstance(orig, HStream), orig

        # if not part.isLastPart():
        #    raise NotImplementedError()

        if not len(orig.start_offsets) == 1:
            raise NotImplementedError()

        din = self.dataIn
        is_first_part_in_stream = part.tmpl.parent.bitAddr == part.startOfPart
        if is_first_part_in_stream:
            frame_range = part.tmpl.parent.bitAddr, part.tmpl.parent.bitAddrEnd
            DW = din.DATA_WIDTH
            start_offset = frame_range[0] % DW
            end_rem = frame_range[1] % DW
            if orig.start_offsets != (0,):
                raise NotImplementedError()

            # this is a first part of stream
            # now connect all data for each part
            non_data_signals = [din.valid, din.ready, din.last]
            if start_offset == 0 and end_rem == 0:
                pass
            else:
                if dout.USE_STRB:
                    non_data_signals.append(din.strb)
                if dout.USE_KEEP:
                    non_data_signals.append(din.keep)

                assert start_offset % 8 == 0, start_offset
                assert end_rem % 8 == 0, end_rem
                first_word_i = frame_range[0] // DW
                last_word_i = (frame_range[1] - 1) // DW
                first_word_mask = mask((DW - start_offset) // 8) << start_offset // 8
                body_word_mask = mask(DW // 8)

                def set_mask(m):
                    res = []
                    if dout.USE_STRB:
                        res.append(dout.strb(m))
                    if dout.USE_KEEP:
                        res.append(dout.keep(m))
                    return res

                if end_rem == 0:
                    last_word_mask = body_word_mask
                else:
                    last_word_mask = mask(end_rem // 8)
                if first_word_i == last_word_i:
                    # only single word, mask is constant
                    m = first_word_mask & last_word_mask
                    set_mask(m)
                elif first_word_i == last_word_i + 1:
                    # only two words, mask is differnt between word 0 and 1
                    raise NotImplementedError()
                else:
                    # 2+ words, first and body or last and body may be same
                    if first_word_mask == body_word_mask:
                        # last is only word with a special mask
                        If(wordIndex._eq(last_word_i),
                            *set_mask(last_word_mask)
                        ).Else(
                            *set_mask(body_word_mask)
                        )
                    elif last_word_mask == body_word_mask:
                        # first is only word with special mask
                        If(wordIndex._eq(first_word_i),
                            *set_mask(first_word_mask)
                        ).Else(
                            *set_mask(body_word_mask)
                        )
                    else:
                        # first, last, body word have all unique masks
                        Switch(wordIndex)\
                        .Case(first_word_i, set_mask(first_word_mask))\
                        .Case(last_word_i, set_mask(last_word_mask))\
                        .Default(set_mask(body_word_mask))

            dout(din, exclude=non_data_signals)
        is_last_part_in_stream = part.tmpl.parent.bitAddrEnd == part.endOfPart
        if is_last_part_in_stream:
            if wordIndex is None:
                last = 1
            else:
                last = wordIndex._eq(currentWordIndex)
            dout.last(last)

        if is_first_part_in_stream or part.startOfPart % din.DATA_WIDTH == 0:
            # first part in current word
            streamGroup = self._streamNodes.setdefault(dout, OutStreamNodeGroup(wordIndex, currentWordIndex))
            streamGroup.word_range_max = currentWordIndex
            on = OutStreamNodeInfo(self.parent, dout, en, exclusiveEn, streamGroup)
            hsNondes.append(on)

    def connectPart(self,
                    hsNondes: ListOfOutNodeInfos,
                    part: Union[TransPart, ChoicesOfFrameParts],
                    en: Union[RtlSignal, bool],
                    exclusiveEn: Union[RtlSignal, bool],
                    wordIndex: Optional[RtlSignal],
                    currentWordIndex: int):
        """
        Create datamux for a single output word in main fsm
        and colect metainformations for handshake logic
        and strb/keep

        :param hsNondes: list of nodes of handshaked logic
        """
        if isinstance(part, ChoicesOfFrameParts):
            # connect union field
            return self.connectChoicesOfFrameParts(
                hsNondes, part, en, exclusiveEn, wordIndex, currentWordIndex)
        # elif isinstance(part, StreamOfFrameParts):
        #     return self.connectStreamOfFrameParts(
        #                hsNondes, part, en, exclusiveEn, wordIndex)
        elif part.isPadding:
            return

        fieldInfo = part.tmpl.origin[-1]
        if isinstance(fieldInfo, HStream) or (
                isinstance(fieldInfo, HStructField) and
                isinstance(fieldInfo.dtype, HStream)):
            return self.connectStreamOfFrameParts(
                hsNondes, part, en, exclusiveEn, wordIndex, currentWordIndex)

        # connect regular scalar field
        fPartSig = self.getInDataSignal(part)
        assert isinstance(fieldInfo, HStructField), fieldInfo

        try:
            signalsOfParts = self._signalsOfParts[part.tmpl]
        except KeyError:
            signalsOfParts = []
            self._signalsOfParts[part.tmpl] = signalsOfParts

        if wordIndex is not None:
            en = en & wordIndex._eq(currentWordIndex)

        if part.isLastPart():
            # connect all parts in this group to output stream
            signalsOfParts.append(fPartSig)
            tToIntf = self.dataOut._fieldsToInterfaces
            intf = tToIntf[part.tmpl.getFieldPath()]
            intf.data(self.byteOrderCare(
                Concat(
                    *reversed(signalsOfParts)
                ))
            )
            on = OutNodeInfo(self.parent, intf, en, exclusiveEn)
            hsNondes.append(on)
        else:
            # part is not in same word as last part, we have to store it's value
            # to register until the last part arrive
            fPartReg = self.parent._reg(f"{fieldInfo.name:s}_part_{len(signalsOfParts):d}",
                fPartSig._dtype)
            dataVld = self.dataIn.valid & en & exclusiveEn
            If(dataVld,
               fPartReg(fPartSig)
            )
            signalsOfParts.append(fPartReg)
