from hwt.code import If
from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.amba.axis_comp.append import AxiS_append
from hwtLib.amba.axis_comp.fifo import AxiSFifo
from hwtLib.amba.axis_comp.fork import AxiSFork
from hwtLib.amba.axis_comp.mux import AxiSMux
from hwtLib.amba.axis_comp.reg import AxiSReg


class AxiSBuilder(AbstractStreamBuilder):
    """
    Helper class which simplifies building of large stream paths
    @ivar end: actual endpoint where building process will continue
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

    def append(self, axis):
        """
        append frame from "axis" behind frame from actual "end"
        @attention: frames are not merged they are just appended
                    to merge frames use "forge"
        """
        u = AxiS_append(self.getInfCls())
        u._updateParamsFrom(self.end)

        setattr(self.parent, self._findSuitableName("append"), u)
        self._propagateClkRstn(u)

        u.dataIn0 ** self.end
        u.dataIn1 ** axis

        self.lastComp = u
        self.end = u.dataOut

        return self

    def extend(self, listOfAxis):
        """
        For each axi stream from "listOfAxis" append frame behind frame from actual "end"
        """
        for axis in listOfAxis:
            self.append(axis)

        return self
