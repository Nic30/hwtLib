from typing import List, Union, Optional

from hwt.code import If, And, Or
from hwt.hdlObjects.typeShortcuts import hBit
from hwt.interfaces.std import Handshaked, VldSynced
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.interfaceLevel.unit import Unit
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
        self.inInterface.rd ** (ackOfOthers & en & self.en)

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
        self.pendingReg = parent._reg(outInterface._name + "_pending_", defVal=1)

    def exclusiveAck(self):
        en = self.exclusiveEn
        ack = self.ack()
        if en is None:
            return ack
        else:
            return ack & en

    def ack(self) -> RtlSignal:
        ack = self.outInterface.rd

        # if output is not selected in union we do not need to care
        # about it's ready
        # if self.exclusiveEn is not None:
        #     ack = ack | ~self.exclusiveEn
        return ack | ~self.pendingReg

    def sync(self, others: List['OutNodeInfo'], en: RtlSignal):
        en = en & self.en
        if self.exclusiveEn is not None:
            en = en & self.exclusiveEn

        ackOfOthers = getAckOfOthers(self, others)
        myRd = self.outInterface.rd

        If(en,
           If(ackOfOthers & (myRd | ~self.pendingReg),
              self.pendingReg ** 1,
           ).Elif(self.pendingReg & myRd,
              self.pendingReg ** 0
           )
        )

        # value of this node was not consumed and it is enabled
        self.outInterface.vld ** (self.pendingReg & en)

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

    def exclusiveAck(self) -> RtlSignal:
        if self:
            return And(*map(lambda x: x.exclusiveAck(), self))
        else:
            return hBit(1)

    def sync(self, allNodes: List[OutNodeInfo], en: RtlSignal) -> None:
        for node in self:
            if node is not self:
                node.sync(allNodes, en)


class ExclusieveListOfHsNodes(list):

    def ack(self) -> RtlSignal:
        if self:
            return Or(*map(lambda x: x.exclusiveAck(), self))
        else:
            return hBit(1)

    def sync(self, allNodes: List[OutNodeInfo], en: RtlSignal) -> None:
        nodesWithoutMe = list(where(allNodes, lambda x: x is not self))
        for item in self:
            item.sync(nodesWithoutMe, en)


class WordFactory():
    def __init__(self, wordIndexReg: RtlSignal):
        self.words = []
        self.wordIndexReg = wordIndexReg

    def addWord(self, index, hsNodes):
        self.words.append((index, hsNodes))

    def ack(self) -> RtlSignal:
        acks = list(map(lambda x: self.wordIndexReg._eq(x[0]) & x[1].ack(),
                        self.words))
        if acks:
            return Or(*acks)
        else:
            return hBit(1)

    def sync(self, en: RtlSignal) -> None:
        for _wordIndex, nodes in self.words:
            for node in nodes:
                node.sync(nodes, en)

