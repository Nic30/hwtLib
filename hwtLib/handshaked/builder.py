#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.handshaked.fifo import HandshakedFifo
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
    JoinExplicitCls = NotImplemented
    JoinPrioritizedCls = HsJoinPrioritized
    JoinFairCls = HsJoinFairShare
    ResizerCls = HsResizer
    RegCls = HandshakedReg
    SplitCopyCls = HsSplitCopy
    SplitFairCls = HsSplitFair
    SplitPrioritizedCls = HsSplitPrioritized
    SplitSelectCls = HsSplitSelect
