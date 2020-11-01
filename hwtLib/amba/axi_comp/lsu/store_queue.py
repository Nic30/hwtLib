#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat, Switch
from hwt.code_utils import rename_signal
from hwt.hdl.constants import READ, WRITE
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.cache.ram_cumulative_mask import BramPort_withReadMask_withoutClk, \
    RamCumulativeMask, is_mask_byte_unaligned
from hwtLib.amba.axi_comp.cache.utils import apply_write_with_mask
from hwtLib.amba.axi_comp.lsu.fifo_oooread import FifoOutOfOrderReadFiltered
from hwtLib.amba.axi_comp.lsu.interfaces import AxiStoreQueueWriteIntf, AxiStoreQueueWriteTmpIntf
from hwtLib.amba.axi_comp.lsu.store_queue_write_dispatcher import AxiStoreQueueWriteDispatcher
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.oneHotToBin import oneHotToBin


@serializeParamsUniq
class AxiStoreQueue(Unit):
    """
    A buffer which is used for write data from cache.
    It manages:
    * out of order write acknowledge
    * write to read bypass (reading of value which is not yet written in AXI slave)
    * write transaction merging

    .. aafig:
    
                                       +-------------------+   
        +------+                       | speculative read  |
        | s.b  |<----------------+     +---------------+---+
        +------+                 |                     |
                                 |           ----------+
        +------+                 |           V         |
        | s.aw |    AW+W      +--+---------------+     |
        | s.w  +---------+--->| cumulative write |     |
        +------+         |    |   tmp register   |     |
                         |    +----------+-------+     |
                                         |             |                     
                         |   data update |             |     
              CAM lookup |    CAM update V             v     transaction lock    +------------------+
                         |     +-------------------------+   and data read       | AW dispatch      |         +------+
                         +---->|  FIFO Out of Order read |<--------------------->| W data dispatch  +-------->| m.aw |
                               |                         |                       |                  |         | m.w  |
                               +-------------------------+                       +------------------+         +------+
                               +------------+     ^                            
                               |  data ram  |     |                             OoO confirm                   +------+
                               +------------+     +---------------------------------------------------------->| m.b  |
                                                                                                              +------+

    :ivar ID_WIDTH: a parameter which specifies width of axi id signal,
        it also specifies the number of items in this buffer (2**ID_WIDTH)
    :ivar MAX_BLOCK_DATA_WIDTH: specifies maximum data width of RAM
        (used to prevent synthesis problems for tools which can not handle
        too wide memories with byte enable)
    """

    def _config(self):
        AxiStoreQueueWriteDispatcher._config(self)
        self.MAX_BLOCK_DATA_WIDTH = Param(None)

    def _declr(self):
        addClkRstn(self)
        AxiStoreQueueWriteDispatcher.precompute_constants(self)
        with self._paramsShared():
            self.w = w = AxiStoreQueueWriteIntf()
            self.w_in_reg = w_in_reg = HandshakedReg(AxiStoreQueueWriteTmpIntf)
            w.ADDR_WIDTH = w_in_reg.ADDR_WIDTH = self.CACHE_LINE_ADDR_WIDTH
            w.DATA_WIDTH = w_in_reg.DATA_WIDTH = self.CACHE_LINE_SIZE * 8

            # self.r = AxiStoreQueueReadIntf()
            self.m = axi = Axi4()._m()
            axi.HAS_R = False
            
            self.write_dispatch = AxiStoreQueueWriteDispatcher()

        self.ooo_fifo = of = FifoOutOfOrderReadFiltered()
        of.ITEMS = w_in_reg.ITEMS = 2 ** self.ID_WIDTH
        of.KEY_WIDTH = self.CACHE_LINE_ADDR_WIDTH

        self.data_ram = dr = RamCumulativeMask()
        dr.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        # data bits and mask bits extended so the total DW % 8 == 0

        dr.DATA_WIDTH = self.DATA_WIDTH
        dr.ADDR_WIDTH = self.DATA_RAM_INDEX_WIDTH
        dr.PORT_CNT = (WRITE, READ)
        dr.HAS_BE = True

    def data_insert(self, items: BramPort_withReadMask_withoutClk):
        """
        * check if this address is already present in CAM
        * if it is possible to update data in this buffer merge data
        * else allocate new data (insert to CAM on push_ptr)
        * handshaked FIFO write logic

        .. aafig::

            +---+  +----------------+  +---------+  +-----------------------------------+
            | w |->| CAM lookup     |->| tmp reg |->| optional item update              |
            +---+  | tmp reg lookup |  +---------+  | optional CAM update and item push |
                   +----------------+               | optional update of tmp reg        |
                                                    +-----------------------------------+ 

        :note: we must not let data from tmp reg if next w_in has same address (we have to update tmp reg instead)
        """
        w_in = self.w
        w_tmp = self.w_in_reg
        ooo_fifo = self.ooo_fifo
        write_pre_lookup = ooo_fifo.write_pre_lookup
        write_pre_lookup_res = ooo_fifo.write_pre_lookup_res

        write_pre_lookup.data(w_in.addr)
        w_tmp_in = w_tmp.dataIn
        w_tmp_out = w_tmp.dataOut

        # if true it means that the current input write data should be merged with 
        # a content of the w_tmp register
        found_in_tmp_reg = rename_signal(
            self,
            w_tmp_in.vld & w_in.addr._eq(w_tmp_out.addr),
            "found_in_tmp_reg"
        )
        accumulated_mask = rename_signal(self, w_in.mask | w_tmp_out.mask, "accumulated_mask")
        If(w_tmp_out.vld & found_in_tmp_reg,
            # update only bytes selected by w_in mask in tmp reg 
            w_tmp_in.data(apply_write_with_mask(w_tmp_out.data, w_in.data, w_in.mask)),
            w_tmp_in.mask(w_in.mask | w_tmp_out.mask),
            w_tmp_in.mask_byte_unaligned(is_mask_byte_unaligned(accumulated_mask))
        ).Else(
            w_tmp_in.data(w_in.data),
            w_tmp_in.mask(w_in.mask),
            w_tmp_in.mask_byte_unaligned(is_mask_byte_unaligned(w_in.mask))
        )
        w_tmp_in.addr(w_in.addr),
        w_tmp_in.cam_lookup(write_pre_lookup_res.data)

        StreamNode([w_in], [w_tmp_in, write_pre_lookup]).sync()
        write_pre_lookup_res.rd(1)

        # CAM insert
        cam_index_onehot = rename_signal(
            self,
            w_tmp_out.cam_lookup & ooo_fifo.item_valid & ~ooo_fifo.item_write_lock,
            "cam_index_onehot")
        cam_found = rename_signal(self, cam_index_onehot != 0, "cam_found")
        cam_found_index = oneHotToBin(self, cam_index_onehot, "cam_found_index")

        write_execute = ooo_fifo.write_execute
        write_execute.key(w_tmp_out.addr)

        current_empty = rename_signal(self, ~ooo_fifo.item_valid[write_execute.index], "current_empty")
        will_insert_new_item = rename_signal(
            self,
            ~cam_found & ~found_in_tmp_reg & current_empty & write_execute.vld,
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
            items.we(w_tmp_out.mask)
            push_ptr = write_execute.index
        else:
            # iteration over multiple bus words to store a cacheline
            push_offset = self._reg("push_offset", self.word_index_t, def_val=0)
            item_write_start = rename_signal(
                self, will_insert_new_item | (cam_found & w_tmp_out.vld),
                "item_write_start")
            If(w_tmp_out.vld & found_in_tmp_reg,
               push_offset(0),
            ).Elif(items.en.vld & items.en.rd & (item_write_start | (push_offset != 0)),
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

            DIN_W = self.DATA_WIDTH
            WE_W = DIN_W // 8
            Switch(push_offset).add_cases([
                (i, [
                    items.din(
                        w_tmp_out.data[(i + 1) * DIN_W:i * DIN_W],
                    ),
                    items.we(
                        w_tmp_out.mask[(i + 1) * WE_W:i * WE_W],
                    )
                ]) for i in range(self.WORD_OFFSET_MAX + 1)]
            ).Default(
                items.din(None),
                items.we(None),
            )

        If(w_tmp_out.vld & cam_found,
            items.addr(cam_found_index)
        ).Else(
            items.addr(push_ptr)
        )
        items.do_accumulate(w_tmp_out.vld & w_tmp_out.mask_byte_unaligned)
        items.do_overwrite(w_tmp_out.vld & ~cam_found)

        write_confirm = ooo_fifo.write_confirm
        StreamNode(
            masters=[w_tmp_out, write_execute],
            slaves=[items.en],
            extraConds={
                write_execute: rename_signal(self, will_insert_new_item & item_insert_last, "ac_write_en"),
                items.en: rename_signal(self, (~w_in.vld | will_insert_new_item | ~item_insert_first) & 
                    (write_confirm.rd | cam_found), "items_en_en"),
                w_tmp_out: rename_signal(self, found_in_tmp_reg | 
                                         (((write_confirm.rd & current_empty) | cam_found) & item_insert_last),
                                         "w_tmp_out_en")
            },
            skipWhen={
                write_execute: found_in_tmp_reg,
                items.en: found_in_tmp_reg,
            }
        ).sync()
        write_confirm.vld(w_tmp_out.vld & will_insert_new_item & item_insert_last & items.en.rd)

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


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # from hwtLib.mem.ram import XILINX_VIVADO_MAX_DATA_WIDTH

    u = AxiStoreQueue()
    # u.ID_WIDTH = 6
    # u.CACHE_LINE_SIZE = 64
    # u.DATA_WIDTH = 256
    # u.MAX_BLOCK_DATA_WIDTH = XILINX_VIVADO_MAX_DATA_WIDTH

    # u.ID_WIDTH = 2
    # u.CACHE_LINE_SIZE = 4
    # u.DATA_WIDTH = (u.CACHE_LINE_SIZE // 2) * 8

    # u.ADDR_WIDTH = 16
    # u.ID_WIDTH = 2
    # u.CACHE_LINE_SIZE = 4
    # u.DATA_WIDTH = 32
    # u.MAX_BLOCK_DATA_WIDTH = 8

    print(to_rtl_str(u))
