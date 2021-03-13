#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import Concat, If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4_addr, Axi4, Axi4_w, Axi4_b
from hwtLib.mem.ramCumulativeMask import BramPort_withReadMask_withoutClk
from hwtLib.amba.constants import BURST_INCR, PROT_DEFAULT, BYTES_IN_TRANS, \
    LOCK_DEFAULT, CACHE_DEFAULT, QOS_DEFAULT
from hwtLib.common_nonstd_interfaces.index_key_hs import IndexKeyHs
from hwtLib.handshaked.streamNode import StreamNode
from pyMathBitPrecise.bit_utils import mask


@serializeParamsUniq
class AxiWriteAggregatorWriteDispatcher(Unit):
    """
    Use :class:`hwtLib.amba.axi_comp.lsu.fifo_oooread.FifoOutOfOrderReadFiltered` read ports
    to query an AXI transaction info and copy paste this transaction from BRAM to AXI.

    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.ID_WIDTH = Param(6)
        self.CACHE_LINE_SIZE = Param(64)  # [B]

    def precompute_constants(self):
        # number of address bits used to index in a single cache line
        self.CACHE_LINE_OFFSET_BITS = log2ceil(self.CACHE_LINE_SIZE - 1)
        # number of bits for an address withou cacheline offset
        self.CACHE_LINE_ADDR_WIDTH = self.ADDR_WIDTH - self.CACHE_LINE_OFFSET_BITS
        # number of AXI4 words in a single cacheline
        self.BUS_WORDS_IN_CACHE_LINE = ceil(self.CACHE_LINE_SIZE * 8 / self.DATA_WIDTH)
        # number of bits for an index for memory wihich stores all buts words for all transactions
        self.DATA_RAM_INDEX_WIDTH = log2ceil(2 ** self.ID_WIDTH * self.BUS_WORDS_IN_CACHE_LINE - 1)

        if self.BUS_WORDS_IN_CACHE_LINE > 1:
            # we need also one value to know that we send all data and we are waiting on something else
            WORD_OFFSET_W = log2ceil(self.BUS_WORDS_IN_CACHE_LINE)
            self.WORD_OFFSET_MAX = mask(WORD_OFFSET_W)
            # type for a counter of bus words in a single transactions
            self.word_index_t = Bits(WORD_OFFSET_W, signed=False, force_vector=True)

    def _declr(self):
        addClkRstn(self)
        self.precompute_constants()

        # port to pull data from memory
        d = self.data = BramPort_withReadMask_withoutClk()._m()
        d.DATA_WIDTH = self.DATA_WIDTH
        d.ADDR_WIDTH = self.DATA_RAM_INDEX_WIDTH
        d.HAS_W = False
        d.HAS_BE = self.DATA_WIDTH > 8

        # begin the read of the item
        wl = self.read_execute = IndexKeyHs()
        wl.KEY_WIDTH = self.CACHE_LINE_ADDR_WIDTH
        wl.INDEX_WIDTH = self.ID_WIDTH

        # confirm that the item was read and the item in fifo is ready to be used again
        pc = self.read_confirm = Handshaked()._m()
        pc.DATA_WIDTH = self.ID_WIDTH

        # bus to write items to
        with self._paramsShared():
            self.m = Axi4()._m()
            self.m.HAS_R = False

    def _impl(self):
        read_execute = self.read_execute
        m = self.m

        aw_ld = self.dispatch_addr(read_execute.index, read_execute.key, m.aw)
        self.dispatch_data(
            aw_ld, read_execute.index, read_execute.rd, ~read_execute.vld,
            self.data,
            m.aw.ready, m.w
        )
        self.receive_write_confirm(self.m.b, self.read_confirm)

    def dispatch_addr(self, id_to_use: RtlSignal, addr: RtlSignal, a: Axi4_addr):
        """
        * if there is a valid item in buffer dispatch read request
        """

        a_ld = self._sig("a_ld")
        a_tmp = self._reg(
            "ar_tmp",
            HStruct(
                (a.id._dtype, "id"),
                (addr._dtype, "addr"),
                (BIT, "vld"),
            ),
            def_val={"vld": 0}
        )

        If(a_ld,
            a_tmp.id(id_to_use),
            a_tmp.addr(addr),
            a_tmp.vld(1)
        ).Else(
            a_tmp.vld(a_tmp.vld & ~a.ready)
        )
        a.id(a_tmp.id)
        a.addr(Concat(a_tmp.addr, Bits(self.CACHE_LINE_OFFSET_BITS).from_py(0)))

        a.len(self.BUS_WORDS_IN_CACHE_LINE - 1)
        a.burst(BURST_INCR)
        a.prot(PROT_DEFAULT)
        a.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))
        a.lock(LOCK_DEFAULT)
        a.cache(CACHE_DEFAULT)
        a.qos(QOS_DEFAULT)
        a.valid(a_tmp.vld)

        return a_ld

    def dispatch_data(self, aw_ld: RtlSignal, pop_ptr: RtlSignal,
                      pop_req: RtlSignal, pop_wait: RtlSignal,
                      items: BramPort_withReadMask_withoutClk,
                      aw_out_ready: RtlSignal, w_out: Axi4_w):
        """
        * if there is a valid item in buffer dispatch write request and write data
        * handshaked FIFO read logic
        """
        BUS_WORDS_IN_CACHE_LINE = self.BUS_WORDS_IN_CACHE_LINE

        bus_w_first = self._sig("bus_w_first_tmp")
        bus_w_last = self._sig("bus_w_last_tmp")
        w_out_ready = self._sig("w_out_ready")
        bus_ack = rename_signal(self, w_out_ready & (aw_out_ready | ~bus_w_first), "bus_ack")
        aw_ld(bus_ack & bus_w_first & items.en.rd & ~pop_wait)
        pop_req((bus_ack & items.en.rd) & ~pop_wait & bus_w_last)
        items.en.vld(bus_ack & ~pop_wait)

        if BUS_WORDS_IN_CACHE_LINE == 1:
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
            read_data_backup.valid(0),  # always moved to read_data
        ).Elif(read_pending,
            read_data_backup.valid(read_data.valid),
        )

        w_out.data(read_data.data)
        w_out.strb(read_data.strb)
        w_out.last(read_data.last)
        w_out.valid(read_data.valid)

        return r_ack

    def receive_write_confirm(self, b: Axi4_b, read_confirm: Handshaked):
        read_confirm.data(b.id)
        StreamNode([b], [read_confirm]).sync()


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str

    u = AxiWriteAggregatorWriteDispatcher()
    print(to_rtl_str(u))
