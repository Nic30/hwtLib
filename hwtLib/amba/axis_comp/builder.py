from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.amba.axis_comp.fifo import AxiSFifo
from hwtLib.amba.axis_comp.fork import AxiSFork
from hwtLib.amba.axis_comp.mux import AxiSMux
from hwtLib.amba.axis_comp.reg import AxiSReg
from hwt.code import If


class AxiSBuilder(AbstractStreamBuilder):
    """
    Helper class which simplifies building of large stream paths
    """
    FifoCls = AxiSFifo
    ForkCls = AxiSFork
    RegCls = AxiSReg
    MuxCls = AxiSMux

    def resize(self, newDataWidth):
        """
        Change datawidth of axi stream
        """
        from hwtLib.amba.axis_comp.resizer import AxiS_resizer
        return self._genericInstance(AxiS_resizer,
                                     "resize",
                                     lambda u: u.OUT_DATA_WIDTH.set(newDataWidth))

    def startOfFrame(self):
        """
        generate start of frame signal, high when we expect new frame to start
        """
        lastseen = self.parent._reg(self.name + "_sof_lastseen", defVal=1)
        intf = self.end

        ack = intf.valid & intf.ready
        If(ack,
           lastseen ** intf.last
        )

        return lastseen
