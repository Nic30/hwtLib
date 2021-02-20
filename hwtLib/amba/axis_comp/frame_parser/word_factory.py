from typing import Optional

from hwt.code import Or
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hdl.types.defs import BIT


class WordFactory():
    """
    An object which sotres information about synchronization of input words for FrameParser instances
    """

    def __init__(self, wordIndexReg: Optional[RtlSignal]):
        self.words = []
        self.wordIndexReg = wordIndexReg

    def addWord(self, index, hsNodes):
        self.words.append((index, hsNodes))

    def _getAck_no_wordIndex(self, x):
        return x[1].ack()

    def _getAck_with_wordIndex(self, x):
        return self.wordIndexReg._eq(x[0]) & x[1].ack()

    def ack(self) -> RtlSignal:
        if self.wordIndexReg is None:
            getAck = self._getAck_no_wordIndex
        else:
            getAck = self._getAck_with_wordIndex

        acks = [getAck(w) for w in self.words]

        if acks:
            return Or(*acks)
        else:
            return BIT.from_py(1)

    def sync(self, en: RtlSignal, din_vld: RtlSignal) -> None:
        for _wordIndex, nodes in self.words:
            for node in nodes:
                node.sync(nodes, en, din_vld)
