from hwt.code import log2ceil, Concat, If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked, HandshakeSync
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi_comp.cache.utils import CamWithReadPort
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.fifo import Fifo
from hwtLib.common_nonstd_interfaces.index_key_hs import IndexKeyHs


@serializeParamsUniq
class FifoOutOfOrderRead(Unit):
    """
    FIFO where the items can be discarded in out of order manner
    If the item is written with same key the record is merged.
    """

    def _config(self):
        self.ITEMS = Param(64)
        self.KEY_WIDTH = Param(4)

    def _declr(self):
        addClkRstn(self)
        ITEM_INDEX_WIDTH = log2ceil(self.ITEMS - 1)
        
        # check if item is stored in CAM
        pl = self.pre_lookup = Handshaked()
        pl.DATA_WIDTH = self.KEY_WIDTH
        
        # return one-hot encoded index of the previously searched key
        plr = self.pre_lookup_res = Handshaked()._m()
        plr.DATA_WIDTH = self.ITEMS

        # insert to CAM, set valid flag to allocate the item
        i = self.insert = IndexKeyHs()
        i.INDEX_WIDTH = ITEM_INDEX_WIDTH
        i.KEY_WIDTH = self.KEY_WIDTH
        
        # move FIFO writer pointer once the insert is completed
        ic = self.insert_confirm = HandshakeSync()
        ic.DATA_WIDTH = ITEM_INDEX_WIDTH

        # on pop the reader pointer is moved however the space is not cleared until the pop is confirmed
        p = self.pop = IndexKeyHs()._m()
        p.KEY_WIDTH = self.KEY_WIDTH
        p.INDEX_WIDTH = ITEM_INDEX_WIDTH

        # after pop is confirmed the item in FIFO can be reused again
        pc = self.pop_confirm = Handshaked()
        pc.DATA_WIDTH = ITEM_INDEX_WIDTH

        c = self.cam = CamWithReadPort()
        c.ITEMS = self.ITEMS
        c.KEY_WIDTH = self.KEY_WIDTH
        c.USE_VLD_BIT = False  # we maintaining vld flag separately

    def _impl(self):
        propagateClkRstn(self)
        ITEMS = self.ITEMS

        # 1 if item contains valid item which can be read
        item_valid = self._reg("item_valid", Bits(ITEMS), def_val=0)
        # 1 if item can not be update any more (:note: valid=1)
        item_write_lock = self._reg("item_write_lock", Bits(ITEMS), def_val=0)
        
        insert_req, insert_wait = self._sig("insert_req"), self._sig("insert_wait")
        pop_req, pop_wait = self._sig("pop_req"), self._sig("pop_wait")
        
        (insert_en, insert_ptr), (pop_en, pop_ptr) = Fifo.fifo_pointers(
            self, ITEMS,
            (insert_req, insert_wait),
            [(pop_req, pop_wait), ]
        )

        ic = self.insert_confirm
       
        insert_req(ic.vld & ~insert_wait)
        ic.rd(~insert_wait)

        pop = self.pop
        pop_req(pop.rd & ~pop_wait)
        pop.vld(~pop_wait)
        pop.index(pop_ptr)
        self.cam.read.addr(pop_ptr)
        pop.key(self.cam.read.data)

        # out of order pop confirmation
        pc = self.pop_confirm
        pc.rd(1)
        _vld_next = []
        _item_write_lock_next = []
        for i in range(ITEMS):
            vld_next = self._sig("valid_%d_next" % (i))
            item_write_lock_next = self._sig("in_progress_%d_next" % (i))
            If(pc.vld & pc.data._eq(i),
               # this is an item which we are discarding
               vld_next(0),
               item_write_lock_next(0)
            ).Elif(insert_en & insert_ptr._eq(i),
               # this is an item which we will insert
               vld_next(1),
               item_write_lock_next(0),
            ).Elif(pop_ptr._eq(i) | (pop_ptr._eq((i - 1) % ITEMS) & pop_req),
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

        ac = self.cam

        ac.match(self.pre_lookup)

        self.pre_lookup_res.data(ac.out.data & item_valid & item_write_lock)
        StreamNode([ac.out], [self.pre_lookup_res]).sync()

        ac.write.addr(self.insert.index)
        ac.write.data(self.insert.key)
        StreamNode([self.insert], [ac.write]).sync()


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # from hwtLib.mem.ram import XILINX_VIVADO_MAX_DATA_WIDTH

    u = FifoOutOfOrderRead()

    print(to_rtl_str(u))
