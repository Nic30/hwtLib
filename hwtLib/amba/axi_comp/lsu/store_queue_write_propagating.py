#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.constants import READ
from hwt.interfaces.std import Signal, VectSignal, Handshaked
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.amba.axi4 import Axi4_r
from hwtLib.amba.axi_comp.lsu.write_aggregator import AxiWriteAggregator
from hwtLib.amba.constants import RESP_OKAY, RESP_EXOKAY
from hwtLib.common_nonstd_interfaces.addr_hs import AddrHs
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.oneHotToBin import oneHotToBin


class AxiWriteAggregatorWriteTmpIntf(Handshaked):

    def _config(self):
        Handshaked._config(self)
        self.ADDR_WIDTH = Param(32)
        self.ID_WIDTH = Param(4)

    def _declr(self):
        Handshaked._declr(self)
        self.addr = VectSignal(self.ADDR_WIDTH)
        # a flag which tells if the data was valid when the time of snapshot of the original register
        self.valid = Signal()

        self.orig_request_addr = VectSignal(self.ADDR_WIDTH)
        self.orig_request_id = VectSignal(self.ID_WIDTH)
        # a flag which tells if the request address equals the addres in orginal register during the time of the snapshot
        self.orig_request_addr_eq = Signal()
        # a flag which tells if this record is generated from input request or if this is a pipeline flush
        self.orig_request_valid = Signal()


@serializeParamsUniq
class AxiStoreQueueWritePropagating(AxiWriteAggregator):
    """
    An extension of :class:`hwtLib.amba.axi_comp.lsu.write_aggregator.AxiWriteAggregator`
    with an IO for a communication with an :class:`hwtLib.amba.axi_comp.lsu.load_queue.AxiLoadQueue`
    Does the same thing and allows :class:`hwtLib.amba.axi_comp.lsu.load_queue_write_propagating.AxiLoadQueueWritePropagating`
    to speculatively read the data and listen for write transactions.
    The component allows for write to bypass read, which makes it suitable for cumulative operations,
    but more complicated for a generic use.

    :ivar speculative_read_addr: port used for load buffer to speculatively read the data from this component.
        If data is not present the speculative_read_data returns RESP_EXOKAY error.
        The data may also be flushed during the read this is marked with RESP_SLVERR error.
    :ivar speculative_read_data: Read data for speculative read.
    """

    def _declr(self):
        AxiWriteAggregator._declr(self)
        with self._paramsShared():
            self.speculative_read_addr = AddrHs()
            self.speculative_read_data = Axi4_r()._m()

        self.ooo_fifo.HAS_READ_LOOKUP = True
        self.data_ram.PORT_CNT = (*self.data_ram.PORT_CNT, READ)

    def speculative_read_handler(self):
        """
        Connect the speculative_read port to internal storages of the :class:`AxiWriteAggregator`

        We need to handle several cases:

        1. the data is currently in tmp register
        2. the data was in tmp register and now is in data memory
        3. the data is in data memory
        4. the data was in data memory and now it is deallocated
        5. the data was not found anywhere


        Handling of speculative read has following stages:

        1. search input register and main address CAM for data
        2. optionaly load the data from ram
        3. send data to speculative_read_data and set resp to error if was not found
           it may also happen that the data was flushed in the mean time

        .. figure:: ./_static/AxiStoreQueueWritePropagating_speculativeRead.png

        :note: speculative read never block the write channel and thus data may be invalid if the speculative read data is stalled.
            This should be handled in master of speculative read port (Other component which is using this component).
        """
        sra = self.speculative_read_addr

        # CLOCK_PERIOD 0
        ooo_fifo = self.ooo_fifo
        ooo_fifo.read_lookup.data(sra.addr[:self.CACHE_LINE_OFFSET_BITS])

        w_in_reg = self.w_in_reg.dataOut
        w_in_reg_tmp = HObjList(HandshakedReg(AxiWriteAggregatorWriteTmpIntf) for _ in range(2))
        for r in w_in_reg_tmp:
            r._updateParamsFrom(w_in_reg)
            r.ID_WIDTH = self.ID_WIDTH

        self.w_in_reg_tmp = w_in_reg_tmp


        w_i = w_in_reg_tmp[0].dataIn
        w_i.orig_request_addr(sra.addr[:self.CACHE_LINE_OFFSET_BITS])
        w_i.orig_request_addr_eq(w_in_reg.addr._eq(w_i.orig_request_addr))
        w_i.orig_request_id(sra.id)
        w_i.orig_request_valid(sra.vld)
        w_i.addr(w_in_reg.addr)
        w_i.data(w_in_reg.data)
        w_i.valid(w_in_reg.vld)

        StreamNode(
            [sra],
            [ooo_fifo.read_lookup, w_i],
            skipWhen={sra: ~sra.vld}, # flush the pipeline if no request
        ).sync()

        # CLK_PERIOD 1
        read_lookup_res = HsBuilder(self, ooo_fifo.read_lookup_res).buff(1).end
        StreamNode(
            [read_lookup_res, w_in_reg_tmp[0].dataOut],
            [w_in_reg_tmp[1].dataIn]
        ).sync()
        w_in_reg_tmp[1].dataIn(
            w_in_reg_tmp[0].dataOut,
            exclude=[w_in_reg_tmp[1].dataIn.vld,
                     w_in_reg_tmp[1].dataIn.rd])

        in_ram_flag = rename_signal(self, read_lookup_res.data & ooo_fifo.item_valid, "in_ram_flag")
        found_in_ram_flag = self._reg("found_in_ram_flag", def_val=0)
        If(read_lookup_res.vld & read_lookup_res.rd,
           found_in_ram_flag(in_ram_flag != 0)
        )

        ram_r = self.data_ram.port[2]
        ram_r.en.vld(found_in_ram_flag.next)
        ram_r.addr(oneHotToBin(self, in_ram_flag, "in_ram_index"))

        # CLK_PERIOD 2
        srd = self.speculative_read_data
        w_in_reg_tmp_o = w_in_reg_tmp[1].dataOut
        StreamNode(
            [w_in_reg_tmp_o],
            [srd],
            # filter out pipeline flushes
            extraConds={srd: w_in_reg_tmp_o.orig_request_valid},
            skipWhen={srd: ~w_in_reg_tmp_o.orig_request_valid},
        ).sync()

        # read from in_tmp req has to be postponed so we can potentially load the data from ram first
        found_in_actual_w_in_reg = rename_signal(
            self,
            w_in_reg.vld & w_in_reg.addr._eq(w_in_reg_tmp_o.orig_request_addr),
            "spec_read_found_in_actual_w_in_reg")
        w_in_reg_tmp_1_o = w_in_reg_tmp[0].dataOut
        found_in_w_in_reg_1 = rename_signal(
            self,
            w_in_reg_tmp_1_o.vld & w_in_reg_tmp_1_o.valid & w_in_reg_tmp_1_o.addr._eq(w_in_reg_tmp_o.orig_request_addr),
            "spec_read_found_in_w_in_reg_1")
        found_in_write_tmp_reg_2 = rename_signal(
            self,
            w_in_reg_tmp_o.vld & w_in_reg_tmp_o.valid & w_in_reg_tmp_o.orig_request_addr_eq,
            "spec_read_found_in_write_tmp_reg_2")

        srd.id(w_in_reg_tmp_o.orig_request_id)
        If(found_in_actual_w_in_reg,
           # found in tmp register just now
           srd.data(w_in_reg.data),
           srd.resp(RESP_OKAY),
           srd.last(1),
        ).Elif(found_in_w_in_reg_1,
           # found in tmp register in clock cycle -2
           srd.data(w_in_reg_tmp_1_o.data),
           srd.resp(RESP_OKAY),
           srd.last(1),
        ).Elif(found_in_write_tmp_reg_2,
           # found in tmp register in clock cycle -2
           srd.data(w_in_reg_tmp_o.data),
           srd.resp(RESP_OKAY),
           srd.last(1),
        ).Elif(found_in_ram_flag,
           # found in write data memory
           srd.data(ram_r.dout),
           srd.resp(RESP_OKAY),
           srd.last(1),
        ).Else(
           # not found anywhere
           srd.data(None),
           srd.resp(RESP_EXOKAY),
           srd.last(1),
        )

    def _impl(self):
        self.speculative_read_handler()
        AxiWriteAggregator._impl(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    from hwtLib.xilinx.constants import XILINX_VIVADO_MAX_DATA_WIDTH

    u = AxiStoreQueueWritePropagating()
    u.DATA_WIDTH = 512
    u.CACHE_LINE_SIZE = 64
    u.MAX_BLOCK_DATA_WIDTH = XILINX_VIVADO_MAX_DATA_WIDTH
    print(to_rtl_str(u))
