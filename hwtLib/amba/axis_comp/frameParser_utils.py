from typing import List, Union, Optional

from hwt.code import If, And, Or
from hwt.hdl.typeShortcuts import hBit
from hwt.interfaces.std import Handshaked, VldSynced
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


class InNodeInfo():
    """
    Interface has to be ready and handshaked logic should be constructed
    """
    def __init__(self, inInterface: Handshaked, en: RtlSignal):
        self.inInterface = inInterface
        self.en = en

    def sync(self, others: List['OutNodeInfo'], en: RtlSignal):
        ackOfOthers = getAckOfOthers(self, others)
        self.inInterface.rd(ackOfOthers & en & self.en)

    def ack(self) -> RtlSignal:
        return self.inInterface.vld


class InNodeReadOnlyInfo(InNodeInfo):
    """
    Interface has to be ready but handshake logic is not constructed
    """
    def sync(self, others: List['OutNodeInfo'], en: RtlSignal):
        pass


class OutNodeInfo():
    """
    Container for informations about output for handshake logic

    :ivar outInterface: output parsed interface
    :ivar en: enable signal of word
    :ivar exvlusiveEn: enable signal of union member
    :ivar pendingReg: register with flag if this item was consumed
    """
    def __init__(self, parent: Unit,
                 outInterface: Union[Handshaked, VldSynced],
                 en: RtlSignal,
                 exclusiveEn: Optional[RtlSignal]=None):
        self.outInterface = outInterface
        self.en = en
        self.exclusiveEn = exclusiveEn
        self.pendingReg = parent._reg(outInterface._name + "_pending_", def_val=1)
        ack = self.outInterface.rd
        self._ack = parent._sig(outInterface._name + "_ack")
        self._ack(ack | ~self.pendingReg)

    def ack(self) -> RtlSignal:
        # if output is not selected in union we do not need to care
        # about it's ready
        # if self.exclusiveEn is not None:
        #     ack = ack | ~self.exclusiveEn
        return self._ack

    def sync(self, others: List['OutNodeInfo'], en: RtlSignal):
        en = en & self.en
        if self.exclusiveEn is not None:
            en = en & self.exclusiveEn

        ackOfOthers = getAckOfOthers(self, others)

        If(en,
           If(ackOfOthers & self.ack(),
              self.pendingReg(1),
           ).Elif(self.pendingReg & self.outInterface.rd,
              self.pendingReg(0)
           )
        )

        # value of this node was not consumed and it is enabled
        self.outInterface.vld(self.pendingReg & en)

    def __repr__(self):
        return "<OutNodeInfo for %s>" % self.outInterface._name


def getAckOfOthers(self: OutNodeInfo, others: List[OutNodeInfo]):
    ackOfOthers = [hBit(1) if o is self else o.ack() for o in others]
    if ackOfOthers:
        return And(*ackOfOthers)
    else:
        return hBit(1)


class ListOfOutNodeInfos(list):
    def ack(self) -> RtlSignal:
        if self:
            return And(*map(lambda x: x.ack(), self))
        else:
            return hBit(1)

    def sync(self, allNodes: List[OutNodeInfo], en: RtlSignal) -> None:
        nodesWithoutMe = list(where(allNodes, lambda x: x is not self))
        for node in self:
            _allNodes = nodesWithoutMe + self
            node.sync(_allNodes, en)


class ExclusieveListOfHsNodes(list):
    """
    @ivar selectorIntf: selector for this node
    """

    def __init__(self, selectorIntf):
        self.selectorIntf = selectorIntf

    def append(self, selectorVal, item):
        return list.append(self, (selectorVal, item))

    def ack(self) -> RtlSignal:
        ack = hBit(1)
        if self:
            acks = list(map(lambda x: x[1].ack() & self.selectorIntf.data._eq(x[0]), self))
            ack = Or(*acks)

        return ack & self.selectorIntf.vld
        

    def sync(self, allNodes: List[OutNodeInfo], en: RtlSignal) -> None:
        nodesWithoutMe = list(where(allNodes, lambda x: x is not self))
        for index, item in self:
            item.sync(nodesWithoutMe, en)


class WordFactory():
    def __init__(self, wordIndexReg: Optional[RtlSignal]):
        self.words = []
        self.wordIndexReg = wordIndexReg

    def addWord(self, index, hsNodes):
        self.words.append((index, hsNodes))

    def ack(self) -> RtlSignal:
        if self.wordIndexReg is None:
            def getAck(x):
                return x[1].ack()
        else:
            def getAck(x):
                return self.wordIndexReg._eq(x[0]) & x[1].ack()

        acks = list(map(getAck, self.words))
        
        if acks:
            return Or(*acks)
        else:
            return hBit(1)

    def sync(self, en: RtlSignal) -> None:
        for _wordIndex, nodes in self.words:
            for node in nodes:
                node.sync(nodes, en)

