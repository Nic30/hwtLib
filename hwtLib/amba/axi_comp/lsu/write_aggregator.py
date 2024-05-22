#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat
from hwt.code_utils import rename_signal
from hwt.constants import READ, WRITE
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.hwParam import HwParam
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hwModule import HwModule
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.lsu.fifo_oooread import FifoOutOfOrderReadFiltered
from hwtLib.amba.axi_comp.lsu.hIOs import HwIOAxiWriteAggregatorWriteTmp
from hwtLib.amba.axi_comp.lsu.write_aggregator_write_dispatcher import AxiWriteAggregatorWriteDispatcher
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.amba.axis_comp.reg import Axi4SReg
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.oneHotToBin import oneHotToBin
from hwtLib.mem.ramCumulativeMask import BramPort_withReadMask_withoutClk, \
    RamCumulativeMask, is_mask_byte_unaligned


@serializeParamsUniq
class AxiWriteAggregator(HwModule):
    """
    A buffer which is used for write data from cache.

    It manages:

    * out of order write acknowledge
    * write transaction merging

    .. image:: ./_static/AxiWriteAggregator.png

    :ivar ID_WIDTH: a parameter which specifies width of axi id signal,
        it also specifies the number of items in this buffer (2**ID_WIDTH)
    :ivar MAX_BLOCK_DATA_WIDTH: specifies maximum data width of RAM
        (used to prevent synthesis problems for tools which can not handle
        too wide memories with byte enable)

    .. hwt-autodoc:: _example_AxiWriteAggregator
    """

    def _config(self):
        AxiWriteAggregatorWriteDispatcher._config(self)
        self.MAX_BLOCK_DATA_WIDTH = HwParam(None)

    def _declr(self):
        addClkRstn(self)
        AxiWriteAggregatorWriteDispatcher.precompute_constants(self)
        with self._hwParamsShared():
            self.s = s_axi = Axi4()
            s_axi.HAS_R = False

            self.m = m_axi = Axi4()._m()
            m_axi.HAS_R = False

            self.write_dispatch = AxiWriteAggregatorWriteDispatcher()

        self.ooo_fifo = of = FifoOutOfOrderReadFiltered()
        of.ITEMS = 2 ** self.ID_WIDTH
        of.KEY_WIDTH = self.CACHE_LINE_ADDR_WIDTH
        self.data_ram = self._declr_data_ram()

    def _declr_data_ram(self):
        dr = RamCumulativeMask()
        dr.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        # data bits and mask bits extended so the total DW % 8 == 0

        dr.DATA_WIDTH = self.DATA_WIDTH
        dr.ADDR_WIDTH = self.DATA_RAM_INDEX_WIDTH
        dr.PORT_CNT = (WRITE, READ)
        dr.HAS_BE = True
        return dr

    def _addr_to_index(self, addr: RtlSignal):
        return addr[:self.CACHE_LINE_OFFSET_BITS]

    def w_in_tmp_reg_load(self) -> HwIOAxiWriteAggregatorWriteTmp:
        """
        * check if this address is already present in address CAM or w_in_reg
        """
        w_in_aw = self.s.aw
        w_in_w = self.s.w
        w_in_b = Axi4SBuilder(self, self.s.b, master_to_slave=False).buff(latency=(1, 2)).end
        ooo_fifo = self.ooo_fifo
        write_pre_lookup = ooo_fifo.write_pre_lookup
        write_pre_lookup_res = ooo_fifo.write_pre_lookup_res

        write_pre_lookup.data(self._addr_to_index(w_in_aw.addr))

        w_in_reg = Axi4SReg(HwIOAxiWriteAggregatorWriteTmp)
        w_in_reg.ID_WIDTH = self.ID_WIDTH
        w_in_reg.ADDR_WIDTH = self.CACHE_LINE_ADDR_WIDTH
        w_in_reg.DATA_WIDTH = self.DATA_WIDTH
        w_in_reg.ITEMS = self.ooo_fifo.ITEMS
        self.w_in_reg = w_in_reg
        w_tmp_in: HwIOAxiWriteAggregatorWriteTmp = w_in_reg.dataIn
        w_tmp_out: HwIOAxiWriteAggregatorWriteTmp = w_in_reg.dataOut

        # if true it means that the current input write data should be merged with
        # a content of the w_tmp register
        colides_with_last_addr_tick = (w_tmp_out.valid &
                                       w_in_aw.valid &
                                       self._addr_to_index(w_in_aw.addr)._eq(w_tmp_out.addr))
        w_tmp_in.data(w_in_w.data)
        w_tmp_in.strb(w_in_w.strb)
        w_tmp_in.last(w_in_w.last)
        addr_related_inputs = [
            w_tmp_in.id(w_in_aw.id),
            w_tmp_in.addr(self._addr_to_index(w_in_aw.addr)),
            w_tmp_in.colides_with_last_addr(colides_with_last_addr_tick),
            w_tmp_in.cam_lookup(write_pre_lookup_res.data),
            w_tmp_in.mask_byte_unaligned(is_mask_byte_unaligned(w_in_w.strb)),
        ]

        w_in_b.resp(RESP_OKAY)
        write_pre_lookup_res.rd(1)

        if self.BUS_WORDS_IN_CACHE_LINE == 1:
            w_in_b.id(w_in_aw.id)
            sync = StreamNode(
                [w_in_aw, w_in_w],
                [w_tmp_in, write_pre_lookup, w_in_b],
            )
        else:
            w_in_b.id(w_tmp_out.id)
            w_in_first = self._reg("w_first", def_val=1)
            If(w_in_first,
               # new transaction initalization
               * addr_related_inputs,
            ).Else(
                # copy the last values specific for this transaction
                w_tmp_in.id(w_tmp_out.id),
                w_tmp_in.addr(w_tmp_out.addr),
                w_tmp_in.colides_with_last_addr(w_tmp_out.colides_with_last_addr | colides_with_last_addr_tick),
                w_tmp_in.cam_lookup(w_tmp_out.cam_lookup),
                w_tmp_in.mask_byte_unaligned(w_tmp_out.mask_byte_unaligned | is_mask_byte_unaligned(w_in_w.strb)),
            )
            w_in_last = w_in_w.last

            # allow aw and write_pre_lookup only in first word, w_in_b only in last
            sync = StreamNode(
                [w_in_aw, w_in_w],
                [w_tmp_in, write_pre_lookup, w_in_b],
                skipWhen={
                    w_in_aw:~w_in_first,
                    write_pre_lookup:~w_in_first,
                    w_in_b:~w_in_last,
                },
                extraConds={
                    w_in_aw: w_in_first,
                    write_pre_lookup: w_in_first,
                    w_in_b: w_in_last,
                }
            )
            If(sync.ack(),
                w_in_first(w_in_last)
            )
        sync.sync()
        # s_axi_stalling = ~w_in_aw.valid | ~w_in_w.valid | ~w_in_b.ready
        return w_tmp_out

    def resolve_cam_index(self, w_tmp_out: HwIOAxiWriteAggregatorWriteTmp):
        ooo_fifo = self.ooo_fifo
        # CAM insert
        cam_index_onehot_previous = self._reg("cam_index_onehot_previous", w_tmp_out.cam_lookup._dtype)
        cam_index_onehot = rename_signal(
            self,
            w_tmp_out.colides_with_last_addr._ternary(cam_index_onehot_previous, w_tmp_out.cam_lookup) &
            ooo_fifo.item_valid &
            ~ooo_fifo.item_write_lock,
            "cam_index_onehot")
        cam_found = rename_signal(self, cam_index_onehot != 0, "cam_found")
        cam_found_index = oneHotToBin(self, cam_index_onehot, "cam_found_index")

        If(w_tmp_out.valid & w_tmp_out.ready,
           cam_index_onehot_previous(cam_index_onehot)
        )

        return cam_found_index, cam_found

    def data_insert(self, items: BramPort_withReadMask_withoutClk):
        """
        * if it is possible to update data in data_ram of this buffer
        * else allocate new data (insert to address CAM of ooo_fifo) and store data to w_in_reg

        .. figure:: ./_static/AxiWriteAggregator_data_insert.png
        """
        ooo_fifo = self.ooo_fifo
        w_tmp_out = self.w_in_tmp_reg_load()
        cam_found_index, cam_found = self.resolve_cam_index(w_tmp_out)

        write_execute = ooo_fifo.write_execute
        write_execute.key(w_tmp_out.addr)

        current_empty = rename_signal(self, ~ooo_fifo.item_valid[write_execute.index], "current_empty")
        will_insert_new_item = rename_signal(
            self,
            ~cam_found & current_empty & write_execute.vld,
            "will_insert_new_item")

        # store to tmp register (and accumulate if possible)
        item_insert_last = self._sig("item_insert_last")
        item_insert_first = self._sig("item_insert_first")

        # insert word iteration,
        # push data to items RAM
        if self.BUS_WORDS_IN_CACHE_LINE == 1:
            # a cacheline fits in to a single busword, no extracarerequired
            item_insert_last(1)
            item_insert_first(1)
            items.din(w_tmp_out.data)
            items.we(w_tmp_out.strb)
            push_ptr = write_execute.index
        else:
            # iteration over multiple bus words to store a cacheline
            push_offset = self._reg("push_offset", self.word_index_t, def_val=0)
            item_write_start = rename_signal(
                self, will_insert_new_item | (cam_found & w_tmp_out.valid),
                "item_write_start")

            If(items.en.vld & items.en.rd &  # currently writing to data_ram
                (item_write_start | (push_offset != 0)),
                # continue writing the parts of tmp reg to data_ram
                If(push_offset != self.WORD_OFFSET_MAX,
                   push_offset(push_offset + 1)
                ).Else(
                   push_offset(0)
                )
            )
            item_insert_last(push_offset._eq(self.WORD_OFFSET_MAX))
            item_insert_first(push_offset._eq(0))
            cam_found_index = Concat(cam_found_index, push_offset)
            push_ptr = Concat(write_execute.index, push_offset)

            items.din(w_tmp_out.data)
            items.we(w_tmp_out.strb)

        If(w_tmp_out.valid & cam_found,
            items.addr(cam_found_index)
        ).Else(
            items.addr(push_ptr)
        )
        items.do_accumulate(w_tmp_out.valid & (w_tmp_out.mask_byte_unaligned | (w_tmp_out.colides_with_last_addr & cam_found)))
        items.do_overwrite(w_tmp_out.valid & ~cam_found)
        write_confirm = ooo_fifo.write_confirm
        StreamNode(
            masters=[w_tmp_out, write_execute],
            slaves=[items.en],
            extraConds={
                write_execute: rename_signal(self, will_insert_new_item & item_insert_last, "write_exe_en"),
                items.en: rename_signal(
                    self,
                    (will_insert_new_item | ~item_insert_first) &
                    (write_confirm.rd | cam_found),
                     "items_en_en"),
                w_tmp_out: rename_signal(self,
                    (((write_confirm.rd & current_empty) | cam_found)),
                    "w_tmp_out_en")
            },
            skipWhen={
                write_execute:~will_insert_new_item,
            }
        ).sync()
        write_confirm.vld(w_tmp_out.valid &
                          will_insert_new_item &
                          item_insert_last &
                          items.en.rd)

    def _impl(self):
        of = self.ooo_fifo
        data_ram = self.data_ram
        self.data_insert(
            data_ram.port[0]
        )

        wd = self.write_dispatch
        self.m(wd.m)
        data_ram.port[1](wd.data)
        of.read_confirm(wd.read_confirm)
        wd.read_execute(of.read_execute)

        propagateClkRstn(self)


def _example_AxiWriteAggregator():
    m = AxiWriteAggregator()
    m.ID_WIDTH = 2
    m.CACHE_LINE_SIZE = 4
    m.DATA_WIDTH = 32
    m.MAX_BLOCK_DATA_WIDTH = 8

    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    # from hwtLib.xilinx.constants import XILINX_VIVADO_MAX_DATA_WIDTH

    m = _example_AxiWriteAggregator()
    # m.ID_WIDTH = 6
    # m.CACHE_LINE_SIZE = 64
    # m.DATA_WIDTH = 256
    # m.MAX_BLOCK_DATA_WIDTH = XILINX_VIVADO_MAX_DATA_WIDTH

    # m.ID_WIDTH = 2
    # m.CACHE_LINE_SIZE = 4
    # m.DATA_WIDTH = (m.CACHE_LINE_SIZE // 2) * 8

    # m.ADDR_WIDTH = 16
    # m.ID_WIDTH = 2
    # m.CACHE_LINE_SIZE = 4
    # m.DATA_WIDTH = 32
    # m.MAX_BLOCK_DATA_WIDTH = 8

    print(to_rtl_str(m))
