#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked, HandshakeSync, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi_comp.cache.utils import CamWithReadPort
from hwtLib.common_nonstd_interfaces.index_key_hs import IndexKeyHs, \
    IndexKeyInHs
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.fifo import Fifo


@serializeParamsUniq
class FifoOutOfOrderRead(Unit):
    """
    Container of FIFO pointers and flags where the items can be discarded in out of order manner.

    .. figure:: ./_static/FifoOutOfOrderRead.png

    :attention: This component does not contains the item storage, it is just container of such a FIFO logic.

    Item state control scheme:

    * write_confirm: the item is now allocated in the fifo and ready to be read
    * read_execute: the item is locked for updates and is currently being read
    * read_confirm: the item is entirely readed and it is ready to be deallocated

    .. hwt-autodoc::
    """

    def _config(self):
        self.ITEMS = Param(4)
        self.KEY_WIDTH = Param(0)

    def _declr(self):
        addClkRstn(self)
        ITEM_INDEX_WIDTH = log2ceil(self.ITEMS - 1)

        # mark item as complete and ready to be read out
        self.write_confirm = HandshakeSync()

        # begin the read of the item
        # :note: this interface is master as it providesthe information about the read execution
        wl = self.read_execute = IndexKeyHs()._m()
        wl.KEY_WIDTH = self.KEY_WIDTH
        wl.INDEX_WIDTH = ITEM_INDEX_WIDTH

        # confirm that the item was read and the item in fifo is ready to be used again
        pc = self.read_confirm = Handshaked()
        pc.DATA_WIDTH = ITEM_INDEX_WIDTH

    def _impl(self):
        propagateClkRstn(self)
        ITEMS = self.ITEMS

        # 1 if item contains valid item which can be read
        item_valid = self._reg("item_valid", Bits(ITEMS), def_val=0)
        # 1 if item can not be update any more (:note: valid=1)
        item_write_lock = self._reg("item_write_lock", Bits(ITEMS), def_val=0)

        write_req, write_wait = self._sig("write_req"), self._sig("write_wait")
        read_req, read_wait = self._sig("read_req"), self._sig("read_wait")

        (write_en, write_ptr), (read_en, read_ptr) = Fifo.fifo_pointers(
            self, ITEMS,
            (write_req, write_wait),
            [(read_req, read_wait), ]
        )

        write_confirm = self.write_confirm

        write_req(write_confirm.vld & ~write_wait & ~item_valid[write_ptr])
        write_confirm.rd(~write_wait & ~item_valid[write_ptr])

        read_execute = self.read_execute
        read_req(read_execute.rd & ~read_wait)
        read_execute.vld(~read_wait)
        read_execute.index(read_ptr)

        # out of order read confirmation
        pc = self.read_confirm
        pc.rd(1)
        _vld_next = []
        _item_write_lock_next = []
        for i in range(ITEMS):
            vld_next = self._sig(f"valid_{i:d}_next")
            item_write_lock_next = self._sig(f"item_write_lock_{i:d}_next")
            If(pc.vld & pc.data._eq(i),
               # this is an item which we are discarding
               vld_next(0),
               item_write_lock_next(0)
            ).Elif(write_en & write_ptr._eq(i),
               # this is an item which we will write
               vld_next(1),
               item_write_lock_next(0),
            ).Elif(read_ptr._eq(i) | (read_ptr._eq((i - 1) % ITEMS) & read_req),
               # we will start reading this item or we are already reading this item
               vld_next(item_valid[i]),
               item_write_lock_next(item_valid[i]),
            ).Else(
               vld_next(item_valid[i]),
               item_write_lock_next(item_write_lock[i]),
            )
            _vld_next.append(vld_next)
            _item_write_lock_next.append(item_write_lock_next)

        item_valid(Concat(*reversed(_vld_next)))
        item_write_lock(Concat(*reversed(_item_write_lock_next)))

        return item_valid, item_write_lock, (write_en, write_ptr), (read_en, read_ptr)


@serializeParamsUniq
class FifoOutOfOrderReadFiltered(FifoOutOfOrderRead):
    """
    :class:`~.FifoOutOfOrderRead` with an additional cam to filter transactions by same key
    :attention: this component does not contains the item storage, it is just container of such a FIFO logic

    .. figure:: ./_static/FifoOutOfOrderReadFiltered.png

    Item state control scheme:

    * write_execute: preallocate the item for writing (and add key to CAM for filtering)
    * write_confirm: the item is now allocated in the fifo and ready to be read
    * read_execute: the item is locked for updates and is currently being read
    * read_confirm: the item is entirely readed and it is ready to be deallocated


    .. hwt-autodoc::
    """

    def _config(self):
        super(FifoOutOfOrderReadFiltered, self)._config()
        self.KEY_WIDTH = 8
        self.HAS_READ_LOOKUP = Param(False)

    def _declr(self) -> None:
        assert self.KEY_WIDTH > 0
        super(FifoOutOfOrderReadFiltered, self)._declr()

        if self.HAS_READ_LOOKUP:
            # check if item is stored in CAM
            pl = self.read_lookup = Handshaked()
            pl.DATA_WIDTH = self.KEY_WIDTH

            # return one-hot encoded index of the previously searched key
            plr = self.read_lookup_res = Handshaked()._m()
            plr.DATA_WIDTH = self.ITEMS

        # check if item is stored in CAM
        pl = self.write_pre_lookup = Handshaked()
        pl.DATA_WIDTH = self.KEY_WIDTH

        # return one-hot encoded index of the previously searched key
        plr = self.write_pre_lookup_res = Handshaked()._m()
        plr.DATA_WIDTH = self.ITEMS

        self.item_valid = VectSignal(self.ITEMS)._m()
        self.item_write_lock = VectSignal(self.ITEMS)._m()

        # write to CAM, set valid flag to allocate the item
        # :note: this interface is master as it providesthe information about the read execution
        i = self.write_execute = IndexKeyInHs()._m()
        i.INDEX_WIDTH = self.read_execute.INDEX_WIDTH
        i.KEY_WIDTH = self.KEY_WIDTH

        c = self.tag_cam = CamWithReadPort()
        c.ITEMS = self.ITEMS
        c.KEY_WIDTH = self.KEY_WIDTH
        c.USE_VLD_BIT = False  # we maintaining vld flag separately
        if self.HAS_READ_LOOKUP:
            c.MATCH_PORT_CNT = 2

    def _impl(self):
        item_valid, item_write_lock, (_, write_ptr), (_, read_ptr) = super(FifoOutOfOrderReadFiltered, self)._impl()
        self.item_valid(item_valid)
        self.item_write_lock(item_write_lock)

        tc = self.tag_cam

        if self.HAS_READ_LOOKUP:
            tc.match[0](self.write_pre_lookup)

            self.write_pre_lookup_res.data(tc.out[0].data & item_valid & item_write_lock)
            StreamNode([tc.out[0]], [self.write_pre_lookup_res]).sync()

            tc.match[1](self.read_lookup)

            self.read_lookup_res.data(tc.out[1].data & item_valid)
            StreamNode([tc.out[1]], [self.read_lookup_res]).sync()

        else:
            tc.match(self.write_pre_lookup)

            self.write_pre_lookup_res.data(tc.out.data & item_valid & item_write_lock)
            StreamNode([tc.out], [self.write_pre_lookup_res]).sync()

        write_execute = self.write_execute
        tc.read.addr(read_ptr)
        for dst in [write_execute.index, tc.write.addr]:
            dst(write_ptr)
        tc.write.data(write_execute.key)
        StreamNode([], [tc.write, write_execute]).sync()
        self.read_execute.key(tc.read.data)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str

    # u = FifoOutOfOrderRead()
    u = FifoOutOfOrderReadFiltered()
    u.HAS_READ_LOOKUP = True
    print(to_rtl_str(u))
