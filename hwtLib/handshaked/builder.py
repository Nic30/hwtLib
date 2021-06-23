#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.fifoAsync import HsFifoAsync
from hwtLib.handshaked.handshakedToAxiStream import HandshakedToAxiStream
from hwtLib.handshaked.joinFair import HsJoinFairShare
from hwtLib.handshaked.joinPrioritized import HsJoinPrioritized
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.resizer import HsResizer
from hwtLib.handshaked.splitCopy import HsSplitCopy
from hwtLib.handshaked.splitFair import HsSplitFair
from hwtLib.handshaked.splitPrioritized import HsSplitPrioritized
from hwtLib.handshaked.splitSelect import HsSplitSelect


class HsBuilder(AbstractStreamBuilder):
    """
    Helper class which simplifies building of large stream paths
    """
    FifoCls = HandshakedFifo
    FifoAsyncCls = HsFifoAsync
    JoinExplicitCls = NotImplemented
    JoinPrioritizedCls = HsJoinPrioritized
    JoinFairCls = HsJoinFairShare
    ResizerCls = HsResizer
    RegCls = HandshakedReg
    SplitCopyCls = HsSplitCopy
    SplitFairCls = HsSplitFair
    SplitPrioritizedCls = HsSplitPrioritized
    SplitSelectCls = HsSplitSelect

    def to_axis(self, MAX_FRAME_WORDS=None, IN_TIMEOUT=None):
        assert MAX_FRAME_WORDS or IN_TIMEOUT
        DATA_WIDTH = self.end._bit_length() - 2

        def set_params(u: HandshakedToAxiStream):
            u.DATA_WIDTH = DATA_WIDTH
            u.MAX_FRAME_WORDS = MAX_FRAME_WORDS
            u.IN_TIMEOUT = IN_TIMEOUT

        next_self = self._genericInstance(HandshakedToAxiStream, "hsToAxiS", set_params)

        from hwtLib.amba.axis_comp.builder import AxiSBuilder
        return AxiSBuilder(self.parent, next_self.end)
