from hwt.code import If
from hwt.hdl.types.hdlType import HdlType
from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.cdc import AxiSCdc
from hwtLib.amba.axis_comp.fifo import AxiSFifo
from hwtLib.amba.axis_comp.fifo_async import AxiSFifoAsync
from hwtLib.amba.axis_comp.fifo_drop import AxiSFifoDrop
from hwtLib.amba.axis_comp.frame_deparser import AxiS_frameDeparser
from hwtLib.amba.axis_comp.frame_parser import AxiS_frameParser
from hwtLib.amba.axis_comp.reg import AxiSReg
from hwtLib.amba.axis_comp.resizer import AxiS_resizer
from hwtLib.amba.axis_comp.splitCopy import AxiSSplitCopy
from hwtLib.amba.axis_comp.splitSelect import AxiSSpliSelect


class AxiSBuilder(AbstractStreamBuilder):
    """
    Helper class which simplifies building of large stream paths
    """
    FifoCls = AxiSFifo
    FifoAsyncCls = AxiSFifoAsync
    FifoDropCls = AxiSFifoDrop
    RegCdcCls = AxiSCdc
    RegCls = AxiSReg
    SplitCopyCls = AxiSSplitCopy
    SplitSelectCls = AxiSSpliSelect
    ResizerCls = AxiS_resizer

    def resize(self, newDataWidth):
        """
        Change datawidth of axi stream
        """
        def set_OUT_DATA_WIDTH(u):
            u.OUT_DATA_WIDTH = newDataWidth
        return self._genericInstance(AxiS_resizer,
                                     "resize",
                                     set_OUT_DATA_WIDTH)

    def startOfFrame(self):
        """
        generate start of frame signal, high when we expect new frame to start
        """
        lastseen = self.parent._reg(self.name + "_sof_lastseen", def_val=1)
        intf = self.end

        ack = intf.valid & intf.ready
        If(ack,
           lastseen(intf.last)
        )

        return lastseen

    def parse(self, typeToParse):
        """
        :param typeToParse: structuralized type to parse
        :return: interface with parsed data (StructIntf for HStruct f.e.)
        """
        u = AxiS_frameParser(typeToParse)
        u._updateParamsFrom(self.end)

        setattr(self.parent, self._findSuitableName("parser"), u)
        self._propagateClkRstn(u)

        u.dataIn(self.end)

        self.lastComp = u
        self.end = None

        return u.dataOut

    @classmethod
    def forge(cls, parent, typeToForge: HdlType, intfCls: AxiStream,
              setupFn=None, name:str=None):
        """
        generate frame assembler for specified type
        :note: you can set endianity and others in setupFn

        :param parent: unit where generated units should be instantiated
        :param typeToForge: instance of htype used as template for frame to assembly
        :param intfCls: class for output interface
        :param setupFn: setup function for output interface
        :param name: name prefix for generated units
        :return: tuple (builder, interface with forged frame)
        """

        u = AxiS_frameDeparser(typeToForge)
        if setupFn:
            setupFn(u)

        if name is None:
            # name can not be empty due AxiSBuilder initialization without interface
            name = "forged"

        self = AxiSBuilder(parent, None, name)
        setattr(parent, self._findSuitableName("forge"), u)
        self._propagateClkRstn(u)
        self.end = u.dataOut

        self.lastComp = u
        self.end = u.dataOut
        return self, u.dataIn

    def buff_drop(self, items, export_size=False, export_space=False):
        """
        Instanciate a FIFO buffer with externally controlled frame drop functionality
        (use "dataIn_discard" signal)
        """
        def set_params(u: AxiSFifoDrop):
            u.DEPTH = items
            u.EXPORT_SIZE = export_size
            u.EXPORT_SPACE = export_space

        return self._genericInstance(self.FifoDropCls, "buff_drop", set_params)
