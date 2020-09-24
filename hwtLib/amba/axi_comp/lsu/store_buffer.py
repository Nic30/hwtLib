#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import If, log2ceil, Concat, Switch
from hwt.code_utils import rename_signal
from hwt.hdl.constants import READ, WRITE
from hwt.hdl.typeShortcuts import vec
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from pyMathBitPrecise.bit_utils import mask

from hwtLib.amba.axi4 import Axi4, Axi4_w
from hwtLib.amba.axi_comp.lsu.interfaces import AddrDataIntf, \
    AxiStoreBufferWriteIntf, AxiStoreBufferWriteTmpIntf
from hwtLib.amba.axi_comp.cache.ram_cumulative_mask import BramPort_withReadMask_withoutClk,\
    RamCumulativeMask, is_mask_byte_unaligned
from hwtLib.amba.axi_comp.cache.utils import CamWithReadPort, \
    apply_write_with_mask
from hwtLib.amba.constants import BYTES_IN_TRANS, LOCK_DEFAULT, CACHE_DEFAULT, \
    QOS_DEFAULT, BURST_INCR, PROT_DEFAULT
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.oneHotToBin import oneHotToBin
from hwtLib.mem.fifo import Fifo


class AxiStoreBuffer(Unit):
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
                         |   data update |             |                +------------------+
              CAM lookup |    CAM update V             v            +-->| AW dispatch      +--+      +------+
                         |     +-------------------------+          |   +------------------+  +----->| m.aw |
                         +---->|  FIFO Out of Order read |<-------  +   +------------------+      +->| m.w  |
                               |                         |<------------>| W data dispatch  +------+  +------+
                               +-------------------------+              +------------------+
                                                  ^                   
                                                  |                    OoO confirm                   +------+
                                                  +------------------------------------------------->| m.b  |
                                                                                                     +------+

    :ivar ID_WIDTH: a parameter which specifies width of axi id signal,
        it also specifies the number of items in this buffer (2**ID_WIDTH)
    :ivar MAX_BLOCK_DATA_WIDTH: specifies maximum data width of RAM
        (used to prevent synthesis problems for tools which can not handle
        too wide memories with byte enable)
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.ID_WIDTH = Param(6)
        self.CACHE_LINE_SIZE = Param(64)  # [B]
        self.MAX_BLOCK_DATA_WIDTH = Param(None)

    def _declr(self):
        addClkRstn(self)
        self.OFFSET_WIDTH = log2ceil(self.CACHE_LINE_SIZE - 1)
        with self._paramsShared():
            self.w = w = AxiStoreBufferWriteIntf()
            self.w_in_reg = w_in_reg = HandshakedReg(AxiStoreBufferWriteTmpIntf)
            w.ADDR_WIDTH = w_in_reg.ADDR_WIDTH = self.ADDR_WIDTH - self.OFFSET_WIDTH
            w.DATA_WIDTH = w_in_reg.DATA_WIDTH = self.CACHE_LINE_SIZE * 8

            # self.r = AxiStoreBufferReadIntf()
            self.bus = axi = Axi4()._m()
            axi.HAS_R = False

        self.addr_cam = ac = CamWithReadPort()
        ac.ITEMS = w_in_reg.ITEMS = 2 ** self.ID_WIDTH
        ac.KEY_WIDTH = self.ADDR_WIDTH - self.OFFSET_WIDTH
        ac.USE_VLD_BIT = False

        self.BUS_WORDS_IN_CACHELINE = ceil(self.CACHE_LINE_SIZE * 8 / self.DATA_WIDTH)
        self.data_ram = dr = RamCumulativeMask()
        dr.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        # data bits and mask bits extended so the total DW % 8 == 0

        dr.DATA_WIDTH = self.DATA_WIDTH
        dr.ADDR_WIDTH = log2ceil(self.BUS_WORDS_IN_CACHELINE * ac.ITEMS)
        dr.PORT_CNT = (WRITE, READ)
        dr.HAS_BE = True

        if self.BUS_WORDS_IN_CACHELINE > 1:
            WORD_OFFSET_W = log2ceil(self.BUS_WORDS_IN_CACHELINE)
            self.WORD_OFFSET_MAX = mask(WORD_OFFSET_W)
            self.word_index_t = Bits(WORD_OFFSET_W, signed=False, force_vector=True)

    def data_insert(self, item_valid, item_in_progress,
                    push_en, push_ptr, push_req, push_wait,
                    items: BramPort_withReadMask_withoutClk):
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
        ac = self.addr_cam
        
        ac.match.data(w_in.addr)
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
        w_tmp_in.cam_lookup(ac.out.data)

        StreamNode([w_in], [w_tmp_in, ac.match]).sync()
        ac.out.rd(1)

        # CAM insert
        cam_index_onehot = rename_signal(
            self,
            w_tmp_out.cam_lookup & item_valid & ~item_in_progress,
            "cam_index_onehot")
        cam_found = rename_signal(self, cam_index_onehot != 0, "cam_found")
        cam_found_index = oneHotToBin(self, cam_index_onehot, "cam_found_index")
        ac.write.addr(push_ptr)
        ac.write.data(w_tmp_out.addr)

        current_empty = rename_signal(self, ~item_valid[push_ptr], "current_empty")
        will_insert_new_item = rename_signal(
            self,
            ~cam_found & ~found_in_tmp_reg & current_empty & ~push_wait,
            "will_insert_new_item")

        # store to tmp register (and accumulate if possible)
        item_insert_last = self._sig("item_insert_last")
        item_insert_first = self._sig("item_insert_first")

        # insert word iteration,
        # push data to items RAM
        if self.BUS_WORDS_IN_CACHELINE == 1:
            item_insert_last(1)
            item_insert_first(1)
            items.din(w_tmp_out.data)
            items.we(w_tmp_out.mask)

        else:
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
            push_ptr = Concat(push_ptr, push_offset)

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

        StreamNode(
            masters=[w_tmp_out],
            slaves=[ac.write, items.en],
            extraConds={
                ac.write: rename_signal(self, will_insert_new_item & item_insert_last, "ac_write_en"),
                items.en: rename_signal(self, (~w_in.vld | will_insert_new_item | ~item_insert_first) &
                    (~push_wait | cam_found), "items_en_en"),
                w_tmp_out: rename_signal(self, found_in_tmp_reg |
                                         (((~push_wait & current_empty) | cam_found) & item_insert_last),
                                         "w_tmp_out_en")
            },
            skipWhen={
                ac.write: found_in_tmp_reg,
                items.en: found_in_tmp_reg,
            }
        ).sync()

        push_req(w_tmp_out.vld & will_insert_new_item & item_insert_last & items.en.rd)

    def data_dispatch(self, addr_cam_read: AddrDataIntf,
                      pop_en: RtlSignal, pop_ptr: RtlSignal,
                      pop_req: RtlSignal, pop_wait: RtlSignal,
                      items: BramPort_withReadMask_withoutClk):
        """
        * if there is a valid item in buffer dispatch write request and write data
        * handshaked FIFO read logic
        """
        w_out = self.bus.w
        aw = self.bus.aw
        BUS_WORDS_IN_CACHELINE = self.BUS_WORDS_IN_CACHELINE 

        aw_ld = self._sig("aw_ld")

        aw_id_tmp = self._reg("aw_id_tmp", aw.id._dtype)
        aw_addr_tmp = self._reg("aw_addr_tmp", aw.addr._dtype)
        aw_vld_tmp = self._reg("aw_vld_tmp", BIT, def_val=0)
        If(aw_ld,
            aw_addr_tmp(Concat(addr_cam_read.data, vec(0, log2ceil(self.CACHE_LINE_SIZE - 1)))),
            aw_id_tmp(pop_ptr),
            aw_vld_tmp(1)
        ).Else(
            aw_vld_tmp(aw_vld_tmp & ~aw.ready)
        )
        addr_cam_read.addr(pop_ptr)
        aw.id(aw_id_tmp)
        aw.addr(aw_addr_tmp)

        aw.len(BUS_WORDS_IN_CACHELINE - 1)
        aw.burst(BURST_INCR)
        aw.prot(PROT_DEFAULT)
        aw.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))
        aw.lock(LOCK_DEFAULT)
        aw.cache(CACHE_DEFAULT)
        aw.qos(QOS_DEFAULT)
        aw.valid(aw_vld_tmp)

        bus_w_first = self._sig("bus_w_first_tmp")
        bus_w_last = self._sig("bus_w_last_tmp")
        w_out_ready = self._sig("w_out_ready")
        bus_ack = rename_signal(self, w_out_ready & (aw.ready | ~bus_w_first), "bus_ack")
        aw_ld(bus_ack & bus_w_first & items.en.rd & ~pop_wait)
        pop_req((bus_ack & items.en.rd) & ~pop_wait & bus_w_last)
        items.en.vld(bus_ack & ~pop_wait)

        if BUS_WORDS_IN_CACHELINE == 1:
            bus_w_first(1)
            bus_w_last(1)
            items.addr(pop_ptr)
        else:
            # instantiate counter
            pop_offset = self._reg("pop_offset", self.word_index_t, def_val=0)
            If(bus_ack & items.en.rd & ~pop_wait,
                If(pop_offset != self.WORD_OFFSET_MAX,
                   pop_offset(pop_offset + 1)
                ).Else(
                   pop_offset(0)
                )
            )
            bus_w_first(pop_offset._eq(0))
            bus_w_last(pop_offset._eq(self.WORD_OFFSET_MAX))
            items.addr(Concat(pop_ptr, pop_offset))

        w_ack = self.data_ram_read_to_bus_w(items, bus_w_last, w_out)
        w_out_ready(w_ack)
        return aw_ld

    def data_ram_read_to_bus_w(self, items: BramPort_withReadMask_withoutClk,
                               item_last: RtlSignal, w_out: Axi4_w):
        """
        Read write data from data_ram

        :param item_last: the signal with last flag for data (notes a last beat in burst)
            sampled in the same time as an read address
        """
        read_pending = self._reg("read_pending", def_val=0)
        item_last_delayed = self._reg("item_last_delayed0")
        tmp_reg_t = HStruct(
            (w_out.data._dtype, "data"),
            (w_out.strb._dtype, "strb"),
            (BIT, "last"),
            (BIT, "valid"),
        )
        read_data = self._reg("read_data", tmp_reg_t, def_val={"valid": 0})
        # register used to store data which were speculatively read from ram
        # and the data from read_data register was not consumed
        read_data_backup = self._reg("read_data_backup", tmp_reg_t, def_val={"valid": 0})

        r_ack = ~read_data.valid | w_out.ready
        read_pending(items.en.vld & r_ack & items.en.rd)
        If(items.en.vld & items.en.rd,
           item_last_delayed(item_last)
        )

        If(read_pending,
           read_data_backup.data(items.dout),
           read_data_backup.strb(items.dout_mask),
           read_data_backup.last(item_last_delayed),
        )

        If(r_ack,
            If(read_pending,
               read_data.data(items.dout),
               read_data.strb(items.dout_mask),
               read_data.last(item_last_delayed),
               read_data.valid(1),
            ).Else(
               read_data.data(read_data_backup.data),
               read_data.strb(read_data_backup.strb),
               read_data.last(read_data_backup.last),
               read_data.valid(read_data_backup.valid),
            )
        )

        If(w_out.ready | ~read_data.valid,
            read_data_backup.valid(0), # always moved to read_data
        ).Elif(read_pending,
            read_data_backup.valid(read_data.valid),
        )

        w_out.data(read_data.data)
        w_out.strb(read_data.strb)
        w_out.last(read_data.last)
        w_out.valid(read_data.valid)

        return r_ack

    def _impl(self):
        ITEMS = self.addr_cam.ITEMS
        # this item in buffer is valid
        item_valid = self._reg("item_valid", Bits(ITEMS), def_val=0)
        # memory write address and data transaction is dispatched and waiting for write acknowledge
        # :note: it in progress records for same address can not be merged as the transaction is on
        #    the way to main memory
        item_in_progress = self._reg("item_in_progress", Bits(ITEMS), def_val=0)

        push_req, push_wait = self._sig("push_req"), self._sig("push_wait")
        pop_req, pop_wait = self._sig("pop_req"), self._sig("pop_wait")
        (push_en, push_ptr), (pop_en, pop_ptr) = Fifo.fifo_pointers(
            self, ITEMS,
            (push_req, push_wait),
            [(pop_req, pop_wait), ]
        )

        self.data_insert(
            item_valid, item_in_progress,
            push_en, push_ptr, push_req, push_wait,
            self.data_ram.port[0])

        self.data_dispatch(
            self.addr_cam.read,
            pop_en, pop_ptr, pop_req, pop_wait,
            self.data_ram.port[1])

        b = self.bus.b
        b.ready(1)
        _vld_next = []
        _in_progress_next = []
        for i in range(ITEMS):
            vld_next = self._sig("valid_%d_next" % (i))
            in_progress_next = self._sig("in_progress_%d_next" % (i))
            If(b.valid & b.id._eq(i),
               vld_next(0),
               in_progress_next(0)
            ).Elif(push_en & push_ptr._eq(i),
               vld_next(1),
               in_progress_next(pop_ptr._eq(i)),
            ).Elif(pop_ptr._eq(i) | (pop_ptr._eq((i - 1) % ITEMS) & pop_req),
               vld_next(item_valid[i]),
               in_progress_next(item_valid[i]),
            ).Else(
               vld_next(item_valid[i]),
               in_progress_next(item_in_progress[i]),
            )
            _vld_next.append(vld_next)
            _in_progress_next.append(in_progress_next)

        item_valid(Concat(*reversed(_vld_next)))
        item_in_progress(Concat(*reversed(_in_progress_next)))

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    #from hwtLib.mem.ram import XILINX_VIVADO_MAX_DATA_WIDTH

    u = AxiStoreBuffer()
    # u.ID_WIDTH = 6
    # u.CACHE_LINE_SIZE = 64
    # u.DATA_WIDTH = 256
    # u.MAX_BLOCK_DATA_WIDTH = XILINX_VIVADO_MAX_DATA_WIDTH

    # u.ID_WIDTH = 2
    # u.CACHE_LINE_SIZE = 4
    # u.DATA_WIDTH = (u.CACHE_LINE_SIZE // 2) * 8

    # u.ADDR_WIDTH = 16
    # u.ID_WIDTH = 2
    # u.CACHE_LINE_SIZE = 8
    # u.DATA_WIDTH = 32
    # u.MAX_BLOCK_DATA_WIDTH = 8

    print(to_rtl_str(u))

