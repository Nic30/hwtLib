from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.reg import HandshakedReg

from hwtLib.handshaked.fork import HandshakedFork
from hwtLib.handshaked.mux import HandshakedMux

class HsBuilder(AbstractStreamBuilder):
    """
    Helper class which simplifies building of large stream paths 
    """
    FifoCls = HandshakedFifo
    ForkCls = HandshakedFork
    RegCls  = HandshakedReg
    MuxCls  = HandshakedMux 