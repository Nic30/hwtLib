from typing import Union, Tuple

from hwt.code import If
from hwt.hdl.types.bitsVal import BitsVal
from hwt.hdl.types.hdlType import HdlType
from hwt.interfaces.structIntf import StructIntf
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.cdc import AxiSCdc
from hwtLib.amba.axis_comp.fifo import AxiSFifo
from hwtLib.amba.axis_comp.fifoDrop import AxiSFifoDrop
from hwtLib.amba.axis_comp.fifo_async import AxiSFifoAsync
from hwtLib.amba.axis_comp.frame_deparser import AxiS_frameDeparser
from hwtLib.amba.axis_comp.frame_parser import AxiS_frameParser
from hwtLib.amba.axis_comp.joinPrioritized import AxiSJoinPrioritized
from hwtLib.amba.axis_comp.reg import AxiSReg
from hwtLib.amba.axis_comp.resizer import AxiS_resizer
from hwtLib.amba.axis_comp.splitCopy import AxiSSplitCopy
from hwtLib.amba.axis_comp.splitSelect import AxiSSpliSelect
from hwtLib.amba.axis_comp.storedBurst import AxiSStoredBurst


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
    JoinPrioritizedCls = AxiSJoinPrioritized

    def resize(self, newDataWidth):
        """
        Change data width of axi stream
        """

        def set_OUT_DATA_WIDTH(u):
            if self.master_to_slave:
                u.OUT_DATA_WIDTH = newDataWidth
            else:
                u.DATA_WIDTH = newDataWidth
                u.OUT_DATA_WIDTH = self.end.DATA_WIDTH

        return self._genericInstance(AxiS_resizer,
                                     "resize",
                                     set_OUT_DATA_WIDTH)

    def startOfFrame(self) -> RtlSignal:
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

    def parse(self, typeToParse) -> StructIntf:
        """
        :param typeToParse: structuralized type to parse
        :return: interface with parsed data (e.g. StructIntf for HStruct)
        """
        assert self.master_to_slave
        u = AxiS_frameParser(typeToParse)
        u._updateParamsFrom(self.end)

        setattr(self.parent, self._findSuitableName("parser"), u)
        self._propagateClkRstn(u)

        u.dataIn(self.end)

        self.lastComp = u
        self.end = None

        return u.dataOut

    @classmethod
    def deparse(cls, parent: Unit, typeToForge: HdlType, intfCls: AxiStream,
                setupFn=None, name:str=None) -> Tuple["AxiSBuilder", StructIntf]:
        """
        generate frame assembler for specified type
        :note: you can set endianity and others in setupFn

        :param parent: unit where generated units should be instantiated
        :param typeToForge: instance of HType used as template for frame to assembly
        :param intfCls: class for output interface
        :param setupFn: setup function for output interface
        :param name: name prefix for generated units
        :return: tuple (builder, interface with deparsed frame)
        """
        assert intfCls is AxiStream, intfCls
        u = AxiS_frameDeparser(typeToForge)
        if setupFn:
            setupFn(u)

        if name is None:
            # name can not be empty due AxiSBuilder initialization without interface
            name = "deparsed"

        self = cls(parent, None, name)
        setattr(parent, self._findSuitableName("deparser"), u)
        self._propagateClkRstn(u)
        self.end = u.dataOut

        self.lastComp = u
        self.end = u.dataOut
        return self, u.dataIn

    def buff_drop(self, items:int, export_size=False, export_space=False):
        """
        Instantiate a FIFO buffer with externally controlled frame drop functionality
        (use "dataIn_discard" signal)
        """

        def set_params(u: AxiSFifoDrop):
            u.DEPTH = items
            u.EXPORT_SIZE = export_size
            u.EXPORT_SPACE = export_space

        return self._genericInstance(self.FifoDropCls, "buff_drop", set_params)

    @classmethod
    def constant_frame(cls,
                       parent: Unit,
                       value: Union[bytes, Tuple[Union[int, BitsVal, None], ...]],
                       data_width: int,
                       use_strb:bool=False,
                       use_keep:bool=False,
                       repeat=True,
                       name=None) -> "AxiSBuilder":
        """
        Instantiate a constant buffer which wil produce the frame of specified data
        """
        u = AxiSStoredBurst()
        u.DATA = value
        u.DATA_WIDTH = data_width
        u.USE_STRB = use_strb
        u.USE_KEEP = use_keep
        u.REPEAT = repeat

        if name is None:
            # name can not be empty due AxiSBuilder initialization without interface
            name = "stored_burst"

        self = cls(parent, None, name)
        setattr(parent, self._findSuitableName("stored_burst"), u)
        self._propagateClkRstn(u)
        self.end = u.dataOut

        self.lastComp = u
        self.end = u.dataOut
        return self
