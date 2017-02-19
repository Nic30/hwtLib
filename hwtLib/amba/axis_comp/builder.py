from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.amba.axis_comp.fifo import AxiSFifo
from hwtLib.amba.axis_comp.fork import AxiSFork
from hwtLib.amba.axis_comp.mux import AxiSMux
from hwtLib.amba.axis_comp.reg import AxiSReg


class AxiSBuilder(AbstractStreamBuilder):
    """
    Helper class which simplifies building of large stream paths 
    """
    FifoCls = AxiSFifo
    ForkCls = AxiSFork
    RegCls  = AxiSReg
    MuxCls  = AxiSMux 