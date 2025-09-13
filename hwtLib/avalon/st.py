from typing import Optional, Union

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import BIT
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIOVectSignal, HwIOSignal, HwIORdSync, \
    HwIOVldSync
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtSimApi.hdlSimulator import HdlSimulator


class AvalonST(HwIODataRdVld):
    """
    Avalon stream interface

    :note: handshaked stream with channel, error, sof, eof signal
    
    Based on Avalon Interface Specifications Updated for Intel Quartus Prime Design Suite: 20.1
    https://cdrdv2.intel.com/v1/dl/getContent/667068?fileName=mnl_avalon_spec-683091-667068.pdf
    
    :ivar USE_EMPTY: add "empty" signal which represents the number of symbols that are empty
    :ivar dataBitsPerSymbol: symbol represents minimal unit of transfered data, it is unit for units of "empty" signal
    :ivar readyLatency: if 0 the interface works as a typical (AXI4 Stream) ready/valid handshake.
        if >0 the ready signaling is delayed. The ready cycle is when source received delayed
        ready=1 from the sink, The source may assert valid only in ready cycle (when it is receiving delayed ready=1)
    :note: if readyLatency > the ready is delayed inside of the source and Avalon-ST itself will use non-delayed value
    :ivar readyAllowance: defines how many data can sink capture with ready=False, if it is set to None then readyAllowance=readyLatency
    :note: readyLatency/readyAllowance are parameters of FIFO implemented on sink side
        the "ready" represents "almost-full" of this FIFO,
        readyLatency=almost-full-remaining-size-1,
        readyAllowance=FIFO total size-1. 
        e.g. readyLatency=0, readyAllowance=1 can buffer 1 item with ready=0
    
    .. figure:: ./_static/avalon_st_readyLatency_readyAllowance.png
        Avalon Interface Specifications Updated for Intel Quartus Prime Design Suite: 20.1, https://cdrdv2.intel.com/v1/dl/getContent/667068?fileName=mnl_avalon_spec-683091-667068.pdf
        Figure 27 - anotated
    :attention: if maxChannel of src > dst only frames with low enought number are forwarded if connected in Quartus.
        if src.maxChannel=8, dst.maxChannel=0 then only frames for channel=0 will be forwarded
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        HwIODataRdVld.hwConfig(self)
        self.dataBitsPerSymbol:int = HwParam(8)
        self.maxChannel:int = HwParam(0)
        self.readyLatency:int = HwParam(0)
        self.readyAllowance: Optional[int] = HwParam(None)
        self.ERROR_WIDTH:int = HwParam(0)
        self.USE_EMPTY:bool = HwParam(None)
        self.SUPPORT_ZLP: bool = HwParam(False)
        self.packetsPerClock = HwParam(1)

    @staticmethod
    def _getWidthOfEmpty(SEGMENT_DATA_WIDTH: int, BYTE_WIDTH: int, SUPPORT_ZLP: bool):
        return log2ceil((SEGMENT_DATA_WIDTH // BYTE_WIDTH) + (1 if SUPPORT_ZLP else 0))

    def _getWidthOfEmptyForSelf(self):
        return self._getWidthOfEmpty(self.DATA_WIDTH // self.packetsPerClock, self.dataBitsPerSymbol, self.SUPPORT_ZLP)

    @override
    def hwDeclr(self):
        # :see: Avalon Interface Specifications 5.9.1. Data Transfers Using readyLatency and readyAllowance
        if self.readyAllowance is not None:
            assert self.readyAllowance >= self.readyLatency, (self.readyAllowance, self.readyLatency)
        else:
            self.readyAllowance = self.readyLatency
        if self.USE_EMPTY is None:
            self.USE_EMPTY = self.DATA_WIDTH > self.dataBitsPerSymbol or self.SUPPORT_ZLP

        # fundamentals
        if self.maxChannel:
            self.channel = HwIOVectSignal(log2ceil(self.maxChannel))

        self.data = HwIOVectSignal(self.DATA_WIDTH)
        if self.USE_EMPTY:
            self.empty = HwIOVectSignal(self._getWidthOfEmptyForSelf())
        if self.ERROR_WIDTH:
            self.error = HwIOVectSignal(self.ERROR_WIDTH)
        # packet transfer signals
        pktSignalT = BIT if self.packetsPerClock else HBits(self.packetsPerClock)
        self.startOfPacket = HwIOSignal(pktSignalT)
        self.endOfPacket = HwIOSignal(pktSignalT)
        HwIOVldSync.hwDeclr(self)
        HwIORdSync.hwDeclr(self)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AvalonSTAgent(sim, self)


AvalonSTAgentWordType = Union[
    # (channel?, data, error?, startOfPacket, endOfPacket)
    tuple[HBitsConst, HBitsConst, HBitsConst, HBitsConst, HBitsConst],
    tuple[HBitsConst, HBitsConst, HBitsConst, HBitsConst],
    tuple[HBitsConst, HBitsConst, HBitsConst],
]


class AvalonSTAgent(HwIODataRdVldAgent):
    """
    Simulation Agent for AvalonST interface
    Data is stored in .data property and data format
    is tuple
    """

    def __init__(self, sim: HdlSimulator, hwIO: AvalonST, allowNoReset=False):
        if hwIO.readyAllowance:
            raise NotImplementedError(hwIO)
        if hwIO.readyLatency != 0:
            raise NotImplementedError(hwIO)
        HwIODataRdVldAgent.__init__(self, sim, hwIO, allowNoReset)

    @override
    def get_data(self) -> AvalonSTAgentWordType:
        hwIO = self.hwIO
        d = []
        if hwIO.maxChannel:
            d.append(hwIO.channel.read())
        d.append(hwIO.data.read())
        if hwIO.USE_EMPTY:
            d.append(hwIO.empty.read())
        if hwIO.ERROR_WIDTH:
            d.append(hwIO.error.read())

        d.append(hwIO.startOfPacket.read())
        d.append(hwIO.endOfPacket.read())
        return tuple(d)

    @override
    def set_data(self, data: Optional[AvalonSTAgentWordType]):
        hwIO = self.hwIO
        if data is None:
            if hwIO.maxChannel:
                hwIO.channel.write(None)
            hwIO.data.write(None)
            if hwIO.USE_EMPTY:
                hwIO.empty.write(None)
            if hwIO.ERROR_WIDTH:
                hwIO.error.write(None)
            hwIO.endOfPacket.write(None)
            hwIO.startOfPacket.write(None)
        else:
            i = 0
            if hwIO.maxChannel:
                hwIO.channel.write(data[0])
                i = 1
            hwIO.data.write(data[i])
            i += 1
            if hwIO.USE_EMPTY:
                hwIO.empty.write(data[i])
                i += 1
            if hwIO.ERROR_WIDTH:
                hwIO.error.write(data[i])
                i += 1

            hwIO.startOfPacket.write(data[i])
            hwIO.endOfPacket.write(data[i + 1])
            assert len(data) == i + 2, (len(data), i + 2)
