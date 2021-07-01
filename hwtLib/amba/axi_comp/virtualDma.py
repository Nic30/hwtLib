from typing import Union, Optional, List

from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.interfaces.std import Handshaked
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSource
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.componentBuilder import AbstractComponentBuilder
from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axi3Lite import Axi3Lite
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.datapump.r import Axi_rDatapump
from hwtLib.amba.datapump.utils import connectDp
from hwtLib.structManipulators.structReader import StructReader
from hwtLib.structManipulators.structWriter import StructWriter
from hwtLib.amba.datapump.w import Axi_wDatapump


class AxiVirtualDma(AbstractComponentBuilder):
    """
    An object which can be used to generate read/write logic for AMBA AXI interfaces.
    It does these things:

    * Based on alignment of the data and data type it optimizes shift logic for alignment
    * If transaction can spawn over multiple AXI transactions it also generates the logic
      for dispatching and merging of such a transactions.
    * It propagates read/write/aligmnent and input errors as a hwt InHwExceptions

    :ivar alignas: specifies alignment requirement for a data type t (in bits),
        same functionailty as C++11 alignas specifier, used to discard alignment logic
    """

    def __init__(self,
                 axi: Union[Axi3, Axi3Lite, Axi4, Axi4Lite],
                 alignas: int=8,
                 max_trans_overlap=16,
        ):
        """
       :param axi: AMBA AXI bus used to read the data
        """
        self.alignas = alignas
        self.max_trans_overlap = max_trans_overlap
        p = axi
        while p._parent is not None:
            p = p._parent
        assert isinstance(p, Unit), p
        AbstractComponentBuilder.__init__(self, p, axi, 'AxiVirtualDma')

    def read(self,
             t: HdlType,
             tmpl: Optional[TransTmpl]=None,
             frames: Optional[List[FrameTmpl]]=None,
             transaction_id=0) -> Union[UnionSource, StructIntf, Handshaked]:
        """
        :param ~.t: instance of HStruct which specifies data format to download
        :param ~.tmpl: instance of TransTmpl for this t
        :param ~.frames: list of FrameTmpl instances for this tmpl
        :param ~.transaction_id: id value for axi
        :note: if tmpl and frames are None they are resolved from structT parseTemplate
        :note: A single transaction can be split to multiple frames, if they are specified by "frames".
        """
        axi = self.end

        r = StructReader(t, tmpl=tmpl, frames=frames)
        r.ID_WIDTH = 0
        r.ADDR_WIDTH = axi.ADDR_WIDTH
        r.DATA_WIDTH = axi.DATA_WIDTH

        setattr(self.parent, self._findSuitableName("rReader"), r)
        self._propagateClkRstn(r)

        dp = Axi_rDatapump(axi.__class__)
        dp.ADDR_WIDTH = axi.ADDR_WIDTH
        dp.ID_WIDTH = axi.ID_WIDTH
        dp.DATA_WIDTH = axi.DATA_WIDTH
        dp.USE_STRB = False
        dp.ID_VAL = transaction_id
        dp.MAX_TRANS_OVERLAP = self.max_trans_overlap
        dp.ALIGNAS = self.alignas

        if isinstance(t, HStream):
            raise NotImplementedError()
        else:
            dp.MAX_CHUNKS = 1
            dp.CHUNK_WIDTH = r.rDatapump.MAX_BYTES * 8

        setattr(self.parent, self._findSuitableName("rDataPump"), dp)
        self._propagateClkRstn(dp)

        connectDp(self.parent, r, dp, self.end)
        return r.get, r.dataOut

    # def read_to_reg(self, t: HdlType, dst: Union[RtlSyncSignal, StructIntf],
    #                ready: RtlSignal, id_=0,
    #                tmpl: Optional[TransTmpl]=None,
    #                frames: Optional[List[FrameTmpl]]=None
    #                ):
    #    """
    #    :note: same as :meth:`AxiMemRead.read` just store the result in to a register.
    #
    #    :returns: signal which is 1 when last part of the data is beeing stored in to thes register.
    #    """
    #
    #    return addr, last
    #
    # def read_out_of_order(self, t: HdlType, allocate, receive, deallocate,
    #                      tmpl: Optional[TransTmpl]=None,
    #                      frames: Optional[List[FrameTmpl]]=None,
    #                      ):
    #    """
    #    Rest of the paramters described in :meth:`~.AxiMemRead.read`
    #    """
    #
    #    return addr, rData
    #
    # def read_out_of_order_to_reg(self, t: HdlType, allocate, receive, deallocate,
    #                             dst: Union[RtlSyncSignal, StructIntf], ready: RtlSignal,
    #                             tmpl: Optional[TransTmpl]=None,
    #                             frames: Optional[List[FrameTmpl]]=None,
    #                             ):
    #    return addr, id, last

    def write(self, t: HdlType, id_=0,
              tmpl: Optional[TransTmpl]=None,
              frames: Optional[List[FrameTmpl]]=None,):
        """
        Rest of the paramters described in :meth:`~.AxiMemRead.read`
        """
        axi = self.end

        w = StructWriter(t, tmpl=tmpl, frames=frames)
        w.ID_WIDTH = 0
        w.ADDR_WIDTH = axi.ADDR_WIDTH
        w.DATA_WIDTH = axi.DATA_WIDTH
        w.USE_STRB = True

        setattr(self.parent, self._findSuitableName("wWriter"), w)
        self._propagateClkRstn(w)

        dp = Axi_wDatapump(axi.__class__)
        dp.ADDR_WIDTH = axi.ADDR_WIDTH
        dp.ID_WIDTH = axi.ID_WIDTH
        dp.DATA_WIDTH = axi.DATA_WIDTH
        dp.ID_VAL = id_
        dp.MAX_TRANS_OVERLAP = self.max_trans_overlap
        dp.ALIGNAS = self.alignas

        if isinstance(t, HStream):
            raise NotImplementedError()
        else:
            dp.MAX_CHUNKS = 1
            dp.CHUNK_WIDTH = w.wDatapump.MAX_BYTES * 8

        setattr(self.parent, self._findSuitableName("wDataPump"), dp)
        self._propagateClkRstn(dp)

        connectDp(self.parent, w, dp, self.end)
        return w.set, w.dataIn, w.writeAck

    def build(self):
        """
        Build an DMA logic from previously stacked reads/writes

        :note: placeholder for future use
        """

