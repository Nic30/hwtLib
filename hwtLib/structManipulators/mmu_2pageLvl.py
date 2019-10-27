#!/usr/bin/env python3
# -*- coding: utf-8 -

from hwt.code import log2ceil, connect, Concat, If
from hwt.interfaces.std import Handshaked, BramPort_withoutClk, \
    Signal
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_comp.axi_datapump_intf import AxiRDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.ramAsHs import RamAsHs
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.ram import RamSingleClock
from hwtLib.structManipulators.arrayItemGetter import ArrayItemGetter


FLAG_INVALID = 1


# http://infocenter.arm.com/help/index.jsp?topic=/com.arm.doc.ddi0301h/I1026235.html
class MMU_2pageLvl(Unit):
    """
    MMU where parent page table is stored in ram this unit
    and only items from leaf page tables are download on each request
    over rDatapump interface

    :attention: if item in pagetable is BAD_PHYS_ADDR output signal segfault becomes 1
                and unit will stop working
    :attention: rootPageTable has to be initialized before first request
               over virtIn interface
    :attention: rootPageTable has write only access
    :attention: use value -1 to mark that page is not mapped, it will result in segfault signal asserted high
                when this address is accessed
    
    .. hwt-schematic::
    """
    def _config(self):
        # width of id signal for bus
        self.ID_WIDTH = Param(1)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)

        self.VIRT_ADDR_WIDTH = Param(32)
        self.LVL1_PAGE_TABLE_ITEMS = Param(512)
        self.PAGE_SIZE = Param(int(2 ** 12))

        self.MAX_OVERLAP = Param(16)

    def _declr(self):
        self.PAGE_OFFSET_WIDTH = log2ceil(self.PAGE_SIZE)
        self.LVL1_PAGE_TABLE_INDX_WIDTH = log2ceil(self.LVL1_PAGE_TABLE_ITEMS)
        self.LVL2_PAGE_TABLE_INDX_WIDTH = self.ADDR_WIDTH - self.LVL1_PAGE_TABLE_INDX_WIDTH - self.PAGE_OFFSET_WIDTH
        self.LVL2_PAGE_TABLE_ITEMS = 2 ** int(self.LVL2_PAGE_TABLE_INDX_WIDTH)
        assert self.LVL1_PAGE_TABLE_INDX_WIDTH > 0, self.LVL1_PAGE_TABLE_INDX_WIDTH
        assert self.LVL2_PAGE_TABLE_INDX_WIDTH > 0, self.LVL2_PAGE_TABLE_INDX_WIDTH
        assert self.LVL2_PAGE_TABLE_ITEMS > 1, self.LVL2_PAGE_TABLE_ITEMS

        # public interfaces
        addClkRstn(self)
        with self._paramsShared():
            self.rDatapump = AxiRDatapumpIntf()._m()
            self.rDatapump.MAX_LEN = 1

        i = self.virtIn = Handshaked()
        i.DATA_WIDTH = self.VIRT_ADDR_WIDTH

        i = self.physOut = Handshaked()._m()
        i.DATA_WIDTH = self.ADDR_WIDTH
        self.segfault = Signal()._m()

        self.lvl1Table = BramPort_withoutClk()

        # internal components
        self.lvl1Storage = RamSingleClock()
        self.lvl1Storage.PORT_CNT = 1
        self.lvl1Converter = RamAsHs()
        for u in [self.lvl1Table, self.lvl1Converter, self.lvl1Storage]:
            u.DATA_WIDTH = self.ADDR_WIDTH
            u.ADDR_WIDTH = self.LVL1_PAGE_TABLE_INDX_WIDTH

        with self._paramsShared():
            self.lvl2get = ArrayItemGetter()
        self.lvl2get.ITEM_WIDTH = self.ADDR_WIDTH
        self.lvl2get.ITEMS = self.LVL2_PAGE_TABLE_ITEMS

        self.lvl2indxFifo = HandshakedFifo(Handshaked)
        self.lvl2indxFifo.DEPTH = self.MAX_OVERLAP // 2
        self.lvl2indxFifo.DATA_WIDTH = self.LVL2_PAGE_TABLE_INDX_WIDTH

        self.pageOffsetFifo = HandshakedFifo(Handshaked)
        self.pageOffsetFifo.DEPTH = self.MAX_OVERLAP
        self.pageOffsetFifo.DATA_WIDTH = self.PAGE_OFFSET_WIDTH

    def connectLvl1PageTable(self):
        rpgt = self.lvl1Table
        rootW = self.lvl1Converter.w
        rpgt.dout(None)
        rootW.addr(rpgt.addr)
        wEn = rpgt.en & rpgt.we
        rootW.vld(wEn)
        rootW.data(rpgt.din)

        self.lvl1Storage.a(self.lvl1Converter.ram)

        lvl1read = self.lvl1Converter.r
        return lvl1read

    def connectL1Load(self, lvl1readAddr):
        virtIn = self.virtIn
        lvl2indx = self.lvl2indxFifo.dataIn
        pageOffset = self.pageOffsetFifo

        lvl2indx.data(virtIn.data[(self.LVL2_PAGE_TABLE_INDX_WIDTH 
                                   + self.PAGE_OFFSET_WIDTH):self.PAGE_OFFSET_WIDTH])
        connect(virtIn.data, pageOffset.dataIn.data, fit=True)
        lvl1readAddr.data(virtIn.data[:(self.LVL2_PAGE_TABLE_INDX_WIDTH 
                                           + self.PAGE_OFFSET_WIDTH)])
        StreamNode(masters=[virtIn],
                   slaves=[lvl2indx, lvl1readAddr, pageOffset.dataIn]).sync()

    def connectL2Load(self, lvl2base, segfaultFlag):
        lvl2get = self.lvl2get
        lvl2indx = self.lvl2indxFifo.dataOut

        self.rDatapump(lvl2get.rDatapump)

        lvl2get.base(lvl2base.data)
        lvl2get.index.data(lvl2indx.data)
        StreamNode(masters=[lvl2base, lvl2indx],
                   slaves=[lvl2get.index],
                   extraConds={
                               lvl2get.index:~segfaultFlag
                              }).sync()

    def connectPhyout(self, segfaultFlag):
        phyAddrBase = self.lvl2get.item
        pageOffset = self.pageOffsetFifo.dataOut

        segfault = segfaultFlag | phyAddrBase.data[0]._eq(FLAG_INVALID)
        StreamNode(masters=[phyAddrBase, pageOffset],
                   slaves=[self.physOut],
                   extraConds={self.physOut:~segfault}).sync()

        self.physOut.data(Concat(phyAddrBase.data[:self.PAGE_OFFSET_WIDTH],
                                 pageOffset.data))

    def segfaultChecker(self):
        lvl1item = self.lvl1Converter.r.data
        lvl2item = self.lvl2get.item
        segfaultFlag = self._reg("segfaultFlag", def_val=False)

        def errVal(intf):
            return intf.vld & intf.data[0]._eq(FLAG_INVALID)

        If(errVal(lvl1item) | errVal(lvl2item),
           segfaultFlag(1)
        )

        return segfaultFlag

    def _impl(self):
        propagateClkRstn(self)

        segfaultFlag = self.segfaultChecker()

        lvl1read = self.connectLvl1PageTable()
        self.connectL1Load(lvl1read.addr)
        self.connectL2Load(lvl1read.data, segfaultFlag)
        self.connectPhyout(segfaultFlag)

        self.segfault(segfaultFlag)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = MMU_2pageLvl()
    print(toRtl(u))
