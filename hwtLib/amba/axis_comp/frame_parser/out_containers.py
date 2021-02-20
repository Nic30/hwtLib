from typing import List, Union, Optional

from hwt.code import If, And, Or
from hwt.hdl.types.defs import BIT
from hwt.interfaces.std import Handshaked, VldSynced
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream


class InNodeInfo():
    """
    Interface has to be ready and handshaked logic should be constructed
    """

    def __init__(self, inInterface: Handshaked, en: RtlSignal):
        self.inInterface = inInterface
        self.en = en

    def sync(self, others: List['OutNodeInfo'], en: RtlSignal, in_vld: RtlSignal):
        ackOfOthers = getAckOfOthers(self, others)
        self.inInterface.rd(en & self.en & ackOfOthers & in_vld)

    def ack(self) -> RtlSignal:
        return self.inInterface.vld


class InNodeReadOnlyInfo(InNodeInfo):
    """
    Interface has to be ready but handshake logic is not constructed
    """

    def sync(self, others: List['OutNodeInfo'], en: RtlSignal, in_vld: RtlSignal):
        pass


class OutNodeInfo():
    """
    Container for informations about output for handshake logic

    :ivar ~.outInterface: output parsed interface
    :ivar ~.en: enable signal of word
    :ivar ~.exvlusiveEn: enable signal of union member
    """

    def __init__(self, parent: Unit,
                 outInterface: Union[Handshaked, VldSynced],
                 en: RtlSignal,
                 exclusiveEn: Optional[RtlSignal]):
        self.parent = parent
        self.outInterface = outInterface
        self.en = en
        self.exclusiveEn = exclusiveEn

        self._ready = self.outInterface.rd
        self._ack = parent._sig(outInterface._name + "_ack")
        self._valid = self.outInterface.vld

    def ack(self) -> RtlSignal:
        # if output is not selected in union we do not need to care
        # about it's ready
        # if self.exclusiveEn is not None:
        #     ack = ack | ~self.exclusiveEn
        return self._ack

    def _sync(self, others: List['OutNodeInfo'], en: RtlSignal, din_vld: RtlSignal):
        """
        :return: output validity signal which is checked
            if data from this word was previously consumed
        """
        en_extra = self.en & self.exclusiveEn
        en = en & en_extra
        if self.exclusiveEn is not None:
            en = en & self.exclusiveEn
        if len(others) > 1:
            # used as a flag for the case where data for this part was
            # consumed but some other part was still not
            was_consumed = self.parent._reg(
                self.outInterface._name + "_was_consumed_", def_val=0)
            self._ack(self._ready | was_consumed)
            ackOfOthers = getAckOfOthers(self, others)

            If(en & din_vld,
                If(was_consumed & ackOfOthers,
                   # restart was_consumed because all others were consumed
                   was_consumed(0),
                ).Elif(~ackOfOthers & self._ready,
                   # set was consumed because the data is passed to output
                   # but some other part can not do the same
                   was_consumed(1)
                )
            )

            # value of this node was not consumed and it is enabled
            return en_extra & ~was_consumed
        else:
            assert others[0] is self
            self._ack(self._ready)
            return en_extra

    def sync(self, others: List['OutNodeInfo'], en: RtlSignal, din_vld: RtlSignal):
        vld = self._sync(others, en, din_vld)
        self._valid(en & vld & din_vld)

    def __repr__(self):
        return f"<{self.__class__.__name__:s} for {self.outInterface._name:s}>"


class OutStreamNodeGroup():

    def __init__(self, word_index: Optional[RtlSignal], word_index_start: int):
        self.word_index = word_index
        self.members = []
        self.word_range_min = word_index_start
        self.word_range_max = word_index_start
        self.others_first = []
        self.others_last = []
        self.vld_first = BIT.from_py(0)
        self.vld_last = BIT.from_py(0)


class OutStreamNodeInfo(OutNodeInfo):
    def __init__(self, parent: Unit,
                 outInterface: AxiStream,
                 en: RtlSignal,
                 exclusiveEn: Optional[RtlSignal],
                 streamGroup: OutStreamNodeGroup
                 ):
        self.streamGroup = streamGroup
        self.parent = parent
        self.outInterface = outInterface
        self.en = en
        self.exclusiveEn = exclusiveEn

        self._ready = self.outInterface.ready
        self._ack = parent._sig(outInterface._name + "_ack")
        self._valid = self.outInterface.valid
        streamGroup.members.append(self)

    def is_in_word_range(self, range_min: int, range_max: int):
        if range_min > range_max:
            return False
        w = self.streamGroup.word_index
        if w is None:
            return BIT.from_py(1)
        if range_min == range_max:
            en = w._eq(range_min)
        elif range_min == 0:
            en = (w <= (range_max))
        else:
            en = ((w > (range_min - 1)) & (
                   w <= (range_max)))
        return en

    def sync(self, others: List['OutNodeInfo'], en: RtlSignal, din_vld: RtlSignal):
        g = self.streamGroup
        w = g.word_index
        is_first_stream_member = g.members[0] is self
        is_last_stream_member = g.members[-1] is self
        if is_first_stream_member:
            g.others_first = others
            if not is_last_stream_member:
                g.vld_first = OutNodeInfo._sync(
                    self, others, en & w._eq(g.word_range_min), din_vld)
            # else we will process it later in last member processing

        if is_last_stream_member:
            g.others_last = others
            if g.word_range_min == g.word_range_max:
                en = self.is_in_word_range(g.word_range_min, g.word_range_max)
                return OutNodeInfo.sync(self, others, en, din_vld)
            else:
                # last word != first word
                if len(g.others_last) > 1:
                    g.vld_last = OutNodeInfo._sync(
                        self, others, en & w._eq(g.word_range_max), din_vld)
                else:
                    self._ack(self._ready)

                in_body = self.is_in_word_range(g.word_range_min + 1,
                                                g.word_range_max - 1)

                self._valid(en & din_vld & (g.vld_first | g.vld_last | in_body))

        if not is_first_stream_member and not is_last_stream_member:
            # stream member for body of the frame
            self._ack(self._ready)


def getAckOfOthers(self: OutNodeInfo, others: List[OutNodeInfo]):
    ackOfOthers = [BIT.from_py(1) if o is self else o.ack() for o in others]
    return And(*ackOfOthers)


class ListOfOutNodeInfos(list):

    def ack(self) -> RtlSignal:
        if self:
            return And(*map(lambda x: x.ack(), self))
        else:
            return BIT.from_py(1)

    def sync(self, allNodes: List[OutNodeInfo], en: RtlSignal, din_vld: RtlSignal) -> None:
        nodesWithoutMe = list(where(allNodes, lambda x: x is not self))
        for node in self:
            _allNodes = nodesWithoutMe + self
            node.sync(_allNodes, en, din_vld)


class ExclusieveListOfHsNodes(list):
    """
    @ivar selectorIntf: selector for this node
    """

    def __init__(self, selectorIntf):
        self.selectorIntf = selectorIntf

    def append(self, selectorVal, item):
        return list.append(self, (selectorVal, item))

    def ack(self) -> RtlSignal:
        ack = BIT.from_py(1)
        if self:
            acks = [x[1].ack() & self.selectorIntf.data._eq(x[0])
                    for x in self]
            ack = Or(*acks)

        return ack & self.selectorIntf.vld

    def sync(self, allNodes: List[OutNodeInfo], en: RtlSignal, din_vld: RtlSignal) -> None:
        nodesWithoutMe = list(where(allNodes, lambda x: x is not self))
        for _, item in self:
            item.sync(nodesWithoutMe, en, din_vld)
