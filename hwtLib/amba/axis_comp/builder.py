from typing import Union, Tuple

from hwt.code import If
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.hdlType import HdlType
from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hwModule import HwModule
from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axis_comp.cdc import Axi4SCdc
from hwtLib.amba.axis_comp.fifo import Axi4SFifo
from hwtLib.amba.axis_comp.fifoDrop import Axi4SFifoDrop
from hwtLib.amba.axis_comp.fifo_async import Axi4SFifoAsync
from hwtLib.amba.axis_comp.frame_deparser import Axi4S_frameDeparser
from hwtLib.amba.axis_comp.frame_parser import Axi4S_frameParser
from hwtLib.amba.axis_comp.joinPrioritized import Axi4SJoinPrioritized
from hwtLib.amba.axis_comp.reg import Axi4SReg
from hwtLib.amba.axis_comp.resizer import Axi4S_resizer
from hwtLib.amba.axis_comp.splitCopy import Axi4SSplitCopy
from hwtLib.amba.axis_comp.splitSelect import Axi4SSpliSelect
from hwtLib.amba.axis_comp.storedBurst import Axi4SStoredBurst


class Axi4SBuilder(AbstractStreamBuilder):
    """
    Helper class which simplifies building of large stream paths
    """
    FifoCls = Axi4SFifo
    FifoAsyncCls = Axi4SFifoAsync
    FifoDropCls = Axi4SFifoDrop
    RegCdcCls = Axi4SCdc
    RegCls = Axi4SReg
    SplitCopyCls = Axi4SSplitCopy
    SplitSelectCls = Axi4SSpliSelect
    ResizerCls = Axi4S_resizer
    JoinPrioritizedCls = Axi4SJoinPrioritized

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

        return self._genericInstance(Axi4S_resizer,
                                     "resize",
                                     set_OUT_DATA_WIDTH)

    def startOfFrame(self) -> RtlSignal:
        """
        generate start of frame signal, high when we expect new frame to start
        """
        lastseen = self.parent._reg(self.name + "_sof_lastseen", def_val=1)
        hwIO = self.end

        ack = hwIO.valid & hwIO.ready
        If(ack,
           lastseen(hwIO.last)
        )

        return lastseen

    def parse(self, typeToParse) -> HwIOStruct:
        """
        :param typeToParse: structuralized type to parse
        :return: interface with parsed data (e.g. HwIOStruct for HStruct)
        """
        assert self.master_to_slave
        m = Axi4S_frameParser(typeToParse)
        m._updateHwParamsFrom(self.end)

        setattr(self.parent, self._findSuitableName("parser"), m)
        self._propagateClkRstn(m)

        m.dataIn(self.end)

        self.lastComp = m
        self.end = None

        return m.dataOut

    @classmethod
    def deparse(cls, parent: HwModule, typeToForge: HdlType, hwIO: Axi4Stream,
                setupFn=None, name:str=None) -> Tuple["Axi4SBuilder", HwIOStruct]:
        """
        generate frame assembler for specified type
        :note: you can set endianity and others in setupFn

        :param parent: HwModule where generated units should be instantiated
        :param typeToForge: instance of HType used as template for frame to assembly
        :param hwIO: class for output interface
        :param setupFn: setup function for output interface
        :param name: name prefix for generated units
        :return: tuple (builder, interface with deparsed frame)
        """
        m = Axi4S_frameDeparser(typeToForge)
        if setupFn:
            setupFn(m)

        if name is None:
            # name can not be empty due Axi4SBuilder initialization without interface
            name = "deparsed"

        self = cls(parent, None, name)
        setattr(parent, self._findSuitableName("deparser"), m)
        self._propagateClkRstn(m)
        self.end = m.dataOut

        self.lastComp = m
        self.end = m.dataOut
        return self, m.dataIn

    def buff_drop(self, items:int, export_size=False, export_space=False):
        """
        Instantiate a FIFO buffer with externally controlled frame drop functionality
        (use "dataIn_discard" signal)
        """

        def set_params(u: Axi4SFifoDrop):
            u.DEPTH = items
            u.EXPORT_SIZE = export_size
            u.EXPORT_SPACE = export_space

        return self._genericInstance(self.FifoDropCls, "buff_drop", set_params)

    @classmethod
    def constant_frame(cls,
                       parent: HwModule,
                       value: Union[bytes, Tuple[Union[int, HBitsConst, None], ...]],
                       data_width: int,
                       use_strb:bool=False,
                       use_keep:bool=False,
                       repeat=True,
                       name=None) -> "Axi4SBuilder":
        """
        Instantiate a constant buffer which wil produce the frame of specified data
        """
        m = Axi4SStoredBurst()
        m.DATA = value
        m.DATA_WIDTH = data_width
        m.USE_STRB = use_strb
        m.USE_KEEP = use_keep
        m.REPEAT = repeat

        if name is None:
            # name can not be empty due Axi4SBuilder initialization without interface
            name = "stored_burst"

        self = cls(parent, None, name)
        setattr(parent, self._findSuitableName("stored_burst"), m)
        self._propagateClkRstn(m)
        self.end = m.dataOut

        self.lastComp = m
        self.end = m.dataOut
        return self

    def to_avalonSt(self) -> "AvalonSTBuilder":
        from hwtLib.avalon.st_comp.avalonStBuilder import AvalonSTBuilder
        return AvalonSTBuilder.from_axis(self.parent, self.end, self.name)
