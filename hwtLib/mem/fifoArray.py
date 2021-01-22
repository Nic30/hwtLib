#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal, HandshakeSync
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.common_nonstd_interfaces.addr_data_hs_bidir import AddrInDataOutHs, AddrInDataOutHsAgent
from hwtLib.handshaked.intfBiDirectional import HandshakedBiDirectional, \
    HandshakedBiDirectionalAgent
from hwtLib.logic.binToOneHot import binToOneHot
from hwtLib.logic.oneHotToBin import oneHotToBin
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION
from pyMathBitPrecise.bit_utils import mask


class FifoArrayInsertInterface(HandshakedBiDirectional):
    """

    :ivar ~.append: if append = 1 the item is appended to last list item specified using "addr"
        else new list is created and "addr" value is ignored
    :ivar ~.addr: an address with potential end of the list
    :ivar ~.data: data to store in next list node
    :ivar ~.addr_ret: an address where the item was inserted to

    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.append = Signal()
        self.data = VectSignal(self.DATA_WIDTH)
        # an address where the item was stored
        self.addr_ret = VectSignal(self.ADDR_WIDTH, masterDir=DIRECTION.IN)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = FifoArrayInsertInterfaceAgent(sim, self)


class FifoArrayInsertInterfaceAgent(HandshakedBiDirectionalAgent):
    """
    Simulation agent for :class:`.FifoArrayInsertInterface` interface
    """

    def onMonitorReady(self):
        a = self.dinData.popleft()
        self.intf.addr_ret.write(a)

    def onDriverWriteAck(self):
        a = self.intf.addr_ret.read()
        self.dinData.append(a)

    def get_data(self):
        i = self.intf
        return (i.addr.read(), i.append.read(), i.data.read())

    def set_data(self, data):
        if data is None:
            a, ap, d = (None, None, None)
        else:
            a, ap, d = data
        i = self.intf
        return (i.addr.write(a), i.append.write(ap), i.data.write(d))


class FifoArrayPopInterface(AddrInDataOutHs):
    """
    :ivar ~.addr: the address of the list head to read from:
    :ivar ~.data: the return data which was read
    :ivar ~.last: flag which tell if this node was last in this list
        and thus this list is now empty and deallocated
    :ivar ~.addr_next: address on a next item in this FIFO

    .. hwt-autodoc::
    """

    def _declr(self):
        super(FifoArrayPopInterface, self)._declr()
        self.last = Signal()
        self.addr_next = VectSignal(self.ADDR_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = FifoArrayPopInterfaceAgent(sim, self)


class FifoArrayPopInterfaceAgent(AddrInDataOutHsAgent):
    """
    Simulation agent for :class:`.FifoArrayPopInterfaceAgent` interface
    """

    def set_data(self, data):
        i = self.intf
        if data is None:
            d, last, an = (None, None, None)
        else:
            d, last, an = data

        i.data.write(d)
        i.last.write(last)
        i.addr_next.write(an)

    def get_data(self):
        i = self.intf
        return (i.data.read(), i.last.read(), i.addr_next.read())


class FifoArray(Unit):
    """
    This component is an array of list nodes, which can be used to emulate multiple FIFOs.
    The memory is shared and the number of lists stored in this array is limited only by memory.

    Corresponds to data structure:

    .. code-block:: cpp

        // note that in implementation each part of struct item is stored in separate array
        struct item {
          value_t value;
          item * next;
          bool valid;
          bool last;
        };

        item items[ITEMS];

    :note: The insert_addr is used to pop from specific list.
        The list can be read only from it's head in FIFO order manner.
        Item is last if it's next pointer points on this item.
    :note: DistRAM implementation.
    :note: The pop address is not checked
        it is possible to pop from wrong list if address is specified incorrectly

    .. hwt-autodoc::
    """

    def _config(self):
        self.ITEMS = Param(4)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        assert self.ITEMS > 1, self.ITEMS
        self.addr_t = Bits(log2ceil(self.ITEMS - 1), signed=False)
        self.value_t = Bits(self.DATA_WIDTH)

        addClkRstn(self)
        self.insert = FifoArrayInsertInterface()

        self.pop = FifoArrayPopInterface()._m()
        for i in [self.insert, self.pop]:
            i.ADDR_WIDTH = self.addr_t.bit_length()
            i.DATA_WIDTH = self.value_t.bit_length()

    def _impl(self):
        addr_t = self.addr_t
        value_t = self.value_t
        item_mask_t = Bits(self.ITEMS)

        # bitmap used to quickly detect position of an empty node
        item_valid = self._reg("item_valid", item_mask_t, def_val=0)
        item_last = self._reg("item_last", item_mask_t, def_val=0)
        # an address on where next item should be inserted
        insert_addr_next = self._reg("insert_addr_next", addr_t, def_val=0)
        insert_addr_next(oneHotToBin(self, rename_signal(self, ~item_valid.next, "item_become_invalid")))  # get index of first non valid

        pop = self.pop
        insert = self.insert

        insert.addr_ret(insert_addr_next)
        insert.rd(item_valid != mask(self.ITEMS))

        pop_one_hot = rename_signal(
            self,
            binToOneHot(pop.addr, en=pop.vld & pop.rd),
            "pop_one_hot")
        insert_one_hot = rename_signal(
            self,
            binToOneHot(insert_addr_next, en=insert.vld & insert.rd),
            "insert_one_hot")
        insert_parent_one_hot = rename_signal(
            self,
            binToOneHot(insert.addr, en=insert.vld & insert.rd & insert.append),
            "insert_parent_one_hot")

        item_valid((item_valid & ~pop_one_hot) | insert_one_hot)
        item_last((item_last & ~insert_parent_one_hot) | insert_one_hot)

        values = self._sig("values", value_t[self.ITEMS])
        next_ptrs = self._sig("next_ptrs", addr_t[self.ITEMS])

        If(self.clk._onRisingEdge(),
            If(insert.vld & insert.rd,
               next_ptrs[insert.addr](insert_addr_next),  # append behind parent node at insert_ptr
               values[insert_addr_next](insert.data),
            )
        )
        pop.data(values[pop.addr])
        pop.addr_next(next_ptrs[pop.addr])
        pop.last(item_last[pop.addr] & item_valid[pop.addr])
        pop.vld(item_valid != 0)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = FifoArray()
    print(to_rtl_str(u))
