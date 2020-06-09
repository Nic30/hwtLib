from hwt.code import If, log2ceil, Concat, Switch
from hwt.hdl.constants import READ, WRITE
from hwt.hdl.typeShortcuts import vec
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import BramPort_withoutClk
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from math import ceil
from pyMathBitPrecise.bit_utils import mask

from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.cache.interfaces import AddrDataIntf, \
    AxiStoreBufferWriteIntf, AxiStoreBufferWriteTmpIntf
from hwtLib.amba.axi_comp.cache.utils import CamWithReadPort, \
    apply_write_with_mask
from hwtLib.amba.constants import BYTES_IN_TRANS, LOCK_DEFAULT, CACHE_DEFAULT, \
    QOS_DEFAULT, BURST_INCR, PROT_DEFAULT
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.logic.oneHotToBin import oneHotToBin
from hwtLib.mem.fifo import Fifo
from hwtLib.mem.ram import RamSingleClock, XILINX_VIVADO_MAX_DATA_WIDTH
from hwtLib.handshaked.streamNode import StreamNode
from hwt.code_utils import rename_signal


def add_padding(padding_bits, sig):
    w = sig._dtype.bit_length()
    if padding_bits:
        return Concat(vec(0, padding_bits), sig)
    else:
        return sig


class AxiStoreBuffer(Unit):
    """
    A buffer which is used for write data from cache.
    It manages:
    * out of order write acknowledge
    * write to read bypass (reading of value which is not yet written in AXI slave)
    * write transaction merging

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
            self.w = AxiStoreBufferWriteIntf()
            self.w_in_reg = HandshakedReg(AxiStoreBufferWriteTmpIntf)
            self.w.ADDR_WIDTH = self.w_in_reg.ADDR_WIDTH = self.ADDR_WIDTH - self.OFFSET_WIDTH
            self.w.DATA_WIDTH = self.w_in_reg.DATA_WIDTH = self.CACHE_LINE_SIZE * 8

            # self.r = AxiStoreBufferReadIntf()
            self.bus = axi = Axi4()._m()
            axi.HAS_R = False

        self.addr_cam = ac = CamWithReadPort()
        ac.ITEMS = self.w_in_reg.ITEMS = 2 ** self.ID_WIDTH
        ac.KEY_WIDTH = self.ADDR_WIDTH - self.OFFSET_WIDTH
        ac.USE_VLD_BIT = False

        self.BUS_WORDS_IN_CACHELINE = ceil(self.CACHE_LINE_SIZE * 8 / self.DATA_WIDTH)
        self.data_ram = dr = RamSingleClock()
        dr.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        # data bits and mask bits extended so the total DW % 8 == 0
        self.MASK_W = self.DATA_WIDTH // 8
        self.MASK_PADDING_W = ceil(self.MASK_W / 8) * 8 - self.MASK_W 
        dr.DATA_WIDTH = self.DATA_WIDTH + self.MASK_PADDING_W + self.MASK_W 
        dr.ADDR_WIDTH = log2ceil(self.BUS_WORDS_IN_CACHELINE * ac.ITEMS)
        dr.PORT_CNT = (WRITE, READ)
        dr.HAS_BE = True

        if self.BUS_WORDS_IN_CACHELINE > 1:
            WORD_OFFSET_W = log2ceil(self.BUS_WORDS_IN_CACHELINE)
            self.WORD_OFFSET_MAX = mask(WORD_OFFSET_W)
            self.word_index_t = Bits(WORD_OFFSET_W, signed=False, force_vector=True)

    def data_insert(self, item_valid, item_in_progress,
                    push_en, push_ptr, push_req, push_wait,
                    items: BramPort_withoutClk):
        """
        * check if this address is already present in cam
        * if it is possible to update data in this buffer merge data
        * else alocate new data (insert to cam on push_ptr)
        * handshaked fifo write logic

        .. aafig::

            +---+  +----------------+  +---------+  +-----------------------------------+
            | w |->| cam lookup     |->| tmp reg |->| optional item update              |
            +---+  | tmp reg lookup |  +---------+  | optional cam update and item push |
                   +----------------+               | optional update of tmp reg        |
                                                    +-----------------------------------+ 

        :note: we must not let data from tmp reg if next w_in has same address (we have to update tmp reg instead)
        """
        w_in = self.w
        w_tmp = self.w_in_reg
        ac = self.addr_cam

        current_empty = rename_signal(self, ~item_valid[push_ptr], "current_empty")

        ac.match.data(w_in.addr)
        w_tmp_in = w_tmp.dataIn
        w_tmp_out = w_tmp.dataOut

        # store to tmp register (and accumulate if possible)
        StreamNode([w_in], [w_tmp_in]).sync()

        item_insert_last = self._sig("item_insert_last")
        item_insert_first = self._sig("item_insert_first")

        # if true it means that the current input write data should be merged with 
        # a content ot he w_tmp register
        found_in_tmp_reg = rename_signal(
            self,
            w_in.vld & w_tmp_out.vld & w_in.addr._eq(w_tmp_out.addr) & item_insert_last,
            "found_in_tmp_reg"
        )
        If(found_in_tmp_reg,
            # update only bytes selected by w_in mask in tmp reg 
            w_tmp_in.data(apply_write_with_mask(w_tmp_out.data, w_in.data, w_in.mask)),
            w_tmp_in.mask(w_in.mask | w_tmp_out.mask),
        ).Else(
            w_tmp_in.data(w_in.data),
            w_tmp_in.mask(w_in.mask),
        )
        w_tmp_in.addr(w_in.addr),
        w_tmp_in.cam_lookup(ac.out.data)

        # cam insert
        cam_index_onehot = rename_signal(self, w_tmp_out.cam_lookup & item_valid & ~item_in_progress, "cam_index_onehot")
        cam_found = rename_signal(self, w_tmp_out.vld & (cam_index_onehot != 0), "cam_found")
        cam_found_index = oneHotToBin(self, cam_index_onehot, "cam_found_index")
        ac.write.addr(push_ptr)
        ac.write.data(w_tmp_out.addr)
        ac.write.vld(w_tmp_out.vld & ~cam_found &
                     ~found_in_tmp_reg & current_empty &
                     item_insert_last)
        ac.match.vld(w_in.vld)
        ac.out.rd(1)

        # insert word iteration

        will_insert_new_item = rename_signal(
            self,
            w_tmp_out.vld &
            ~cam_found &
            ~found_in_tmp_reg &
            current_empty &
            ~push_wait,
            "will_insert_new_item")
        item_write_start = rename_signal(
            self, will_insert_new_item | cam_found,
            "item_write_start")

        if self.BUS_WORDS_IN_CACHELINE == 1:
            item_insert_last(1)
            item_insert_first(1)
        else:
            insert_offset = self._reg("insert_offset", self.word_index_t, def_val=0)
            If(item_write_start | (insert_offset != 0),
                If(insert_offset != self.WORD_OFFSET_MAX,
                   insert_offset(insert_offset + 1)
                ).Else(
                   insert_offset(0)
                )
            )
            item_insert_last(insert_offset._eq(self.WORD_OFFSET_MAX))
            item_insert_first(insert_offset._eq(0))
            cam_found_index = Concat(cam_found_index, insert_offset)
            push_ptr = Concat(push_ptr, insert_offset)

        If(cam_found,
            items.addr(cam_found_index)
        ).Else(
            items.addr(push_ptr)
        )
        MASK_W = self.DATA_WIDTH // 8
        TOTAL_MASK_W = self.CACHE_LINE_SIZE
        WE_FOR_WE_W = ceil(MASK_W / 8)
        we_for_mask = vec(mask(WE_FOR_WE_W), WE_FOR_WE_W)
        we_for_data = rename_signal(
            self,
            Concat(*(~push_wait | (cam_found & w_tmp_out.mask[i])
                     for i in reversed(range(TOTAL_MASK_W)))),
            "we_for_data")
        items.en(will_insert_new_item | ~item_insert_first)
        # push data to items RAM
        if self.BUS_WORDS_IN_CACHELINE == 1:
            din = Concat(w_tmp_out.data, add_padding(self.MASK_PADDING_W, w_tmp_out.mask))
            items.din(din)
            items.we(Concat(we_for_data, we_for_mask))

        else:
            DIN_W = self.DATA_WIDTH
            WE_W = DIN_W // 8
            Switch(insert_offset).add_cases([
                (i, [
                    items.din(Concat(
                        w_tmp_out.data[(i + 1) * DIN_W:i * DIN_W],
                        add_padding(self.MASK_PADDING_W, w_tmp_out.mask[(i + 1) * WE_W:i * WE_W]),
                    )),
                    items.we(Concat(
                        we_for_data[(i + 1) * WE_W:i * WE_W],
                        we_for_mask,
                    ))
                ]) for i in range(self.WORD_OFFSET_MAX + 1)]
            ).Default(
                items.din(None),
                items.we(None),
            )

        w_tmp_out.rd(((~push_wait & current_empty) | cam_found) & item_insert_last)
        push_req(will_insert_new_item & item_insert_last)

    def data_dispatch(self, addr_cam_read: AddrDataIntf,
                      pop_en: RtlSignal, pop_ptr: RtlSignal,
                      pop_req: RtlSignal, pop_wait: RtlSignal,
                      items: BramPort_withoutClk):
        """
        * if there is a valid item in buffer dispath write request and write data
        * handshaked fifo read logic
        """
        w_out = self.bus.w
        aw = self.bus.aw
        BUS_WORDS_IN_CACHELINE = self.BUS_WORDS_IN_CACHELINE 

        aw_ld = self._sig("aw_ld")

        aw_id_tmp = self._reg("aw_id_tmp", aw.id._dtype)
        aw_addr_tmp = self._reg("aw_addr_tmp", aw.addr._dtype)
        If(aw_ld,
            aw_addr_tmp(Concat(addr_cam_read.data, vec(0, log2ceil(self.CACHE_LINE_SIZE - 1)))),
            aw_id_tmp(pop_ptr),
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

        bus_w_vld = self._reg("bus_w_vld", def_val=0)
        bus_w_first = self._sig("bus_w_first_tmp")
        bus_w_last = self._sig("bus_w_last_tmp")
        bus_ack = rename_signal(self, w_out.ready & (aw.ready | ~bus_w_first), "bus_ack")
        If(bus_ack | ~bus_w_vld,
           bus_w_vld(~pop_wait)
        )
        bus_ack_or_empty_reg = rename_signal(self, (bus_ack | ~bus_w_vld) & ~pop_wait, "bus_ack_or_empty_reg")
        aw_ld(bus_ack_or_empty_reg & bus_w_first)
        pop_req((bus_ack | ~bus_w_vld) & ~pop_wait & bus_w_last)
        aw.valid(bus_w_vld & w_out.ready & bus_w_first)
        items.en(bus_ack_or_empty_reg)
        w_out.valid(bus_w_vld & (aw.ready | ~bus_w_first))

        if BUS_WORDS_IN_CACHELINE == 1:
            bus_w_first(1)
            bus_w_last(1)
            items.addr(pop_ptr)
            w_out.data(items.dout[:self.MASK_PADDING_W + self.MASK_W])
            w_out.strb(items.dout[self.MASK_W:])
            w_out.last(bus_w_last)
        else:
            # instanciate counter
            pop_offset = self._reg("pop_offset", self.word_index_t, def_val=0)
            If(bus_ack_or_empty_reg & ~pop_wait,
                If(pop_offset != self.WORD_OFFSET_MAX,
                   pop_offset(pop_offset + 1)
                ).Else(
                   pop_offset(0)
                )
            )
            bus_w_first(pop_offset._eq(0))
            bus_w_last(pop_offset._eq(self.WORD_OFFSET_MAX))

            bus_w_last_delayed = self._reg("bus_w_last_delayed")
            bus_w_last_delayed(bus_w_last)
            w_out.last(bus_w_last_delayed)

            items.addr(Concat(pop_ptr, pop_offset))
            w_out.data(items.dout[:self.MASK_PADDING_W + self.MASK_W])
            w_out.strb(items.dout[self.MASK_W:])

        return aw_ld

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
    u = AxiStoreBuffer()
    u.ID_WIDTH = 6
    u.CACHE_LINE_SIZE = 64
    u.DATA_WIDTH = 256
    u.MAX_BLOCK_DATA_WIDTH = XILINX_VIVADO_MAX_DATA_WIDTH
    
    # u.ID_WIDTH = 2
    # u.CACHE_LINE_SIZE = 4
    # u.DATA_WIDTH = (u.CACHE_LINE_SIZE // 2) * 8
    print(to_rtl_str(u))

