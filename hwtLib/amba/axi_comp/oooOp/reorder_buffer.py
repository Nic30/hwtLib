#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple

from hwt.code import If
from hwt.constants import READ, WRITE
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwIOs.hwIOStruct import HwIOStructRdVld
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.hdl.types.bits import HBits
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.rtlLevel.rtlSyncSignal import RtlSyncSignal
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.ramAsAddrDataRdVld import RamAsAddrDataRdVld
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.binToOneHot import binToOneHot
from hwtLib.mem.ram import RamSingleClock
from hwtLib.types.ctypes import uint16_t
from hwtSimApi.hdlSimulator import HdlSimulator
from pyMathBitPrecise.bit_utils import apply_set_and_clear


class HwIOStructRdVldWithId(HwIOStructRdVld):

    def _config(self):
        HwIOStructRdVld._config(self)
        self.ID_WIDTH = HwParam(6)

    def _declr(self):
        self.id = HwIOVectSignal(self.ID_WIDTH)
        HwIOStructRdVld._declr(self)
        
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOStructRdVldWithIdAgent(sim, self)

        
class HwIOStructRdVldWithIdAgent(HwIODataRdVldAgent):

    def get_data(self):
        i = self.hwIO
        return (i.id.read(), i.data.read())

    def set_data(self, data):
        i = self.hwIO
        if data is None:
            t, d = (None, None)
        else:
            t, d = data

        i.id.write(t)
        i.data.write(d)


class ReorderBuffer(HwModule):
    """
    Serialize an unordered input sequence to continuous output sequence.

    :ivar dataIn: an input interface with an id signal which is used to reconstruct the sequence
    :ivar dataOut: an output interface with a data from dataIn which is ordered according to its id

    .. hwt-autodoc::
    """

    def _config(self):
        HwIOStructRdVldWithId._config(self)
        self.T = uint16_t
    
    def _declr(self):
        assert self.T is not None
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = HwIOStructRdVldWithId()
            self.dataOut = HwIOStructRdVld()._m()  
        
        self.storage_w = RamAsAddrDataRdVld()
        self.storage_w.HAS_W = True
        self.storage_w.HAS_R = False
        self.storage_w.ADDR_WIDTH = self.ID_WIDTH;
        self.storage_w.DATA_WIDTH = self.T.bit_length()
        
        self.storage_r = RamAsAddrDataRdVld()
        self.storage_r._updateParamsFrom(self.storage_w)        
        self.storage_r.HAS_R = True
        self.storage_r.HAS_W = False
        
        self.storage_ram = RamSingleClock()
        self.storage_ram._updateParamsFrom(self.storage_w)
        self.storage_ram.PORT_CNT = (WRITE, READ) 

    def item_occupancy_reg(self) -> Tuple[RtlSignal, RtlSyncSignal, RtlSignal]:
        item_occ_set = self._sig("item_occ_set", HBits(2 ** self.ID_WIDTH))
        item_occ_clear = self._sig("item_occ_clear", HBits(2 ** self.ID_WIDTH))
        item_occ = self._reg("item_occ", HBits(2 ** self.ID_WIDTH), def_val=0)
        item_occ(apply_set_and_clear(item_occ, item_occ_set, item_occ_clear))
        return item_occ_set, item_occ, item_occ_clear

    def _impl(self):
        self.storage_ram.port[0](self.storage_w.ram)
        self.storage_ram.port[1](self.storage_r.ram)
        
        dataIn_reg = HsBuilder(self, self.dataIn).buff(1).end
        
        item_occ_set, item_occ, item_occ_clear = self.item_occupancy_reg()
        
        # Input side
        sn_in = StreamNode(
            [dataIn_reg],
            [self.storage_w.w],
            extraConds={dataIn_reg:~(item_occ[dataIn_reg.id])}
        )
        sn_in.sync()
        self.storage_w.w.addr(dataIn_reg.id)
        self.storage_w.w.data(dataIn_reg.data._reinterpret_cast(self.storage_w.w.data._dtype))
        If(sn_in.ack(),
            item_occ_set(binToOneHot(dataIn_reg.id))
        ).Else(
            item_occ_set(0)
        )
        
        # Output
        out_cntr = self._reg("item_occ", HBits(self.ID_WIDTH), def_val=0)
        sn_addr = StreamNode(
            [],
            [self.storage_r.r.addr],
            extraConds={self.storage_r.r.addr: item_occ[out_cntr]}
        )
        sn_addr.sync()
        self.storage_r.r.addr.data(out_cntr)
        If(sn_addr.ack(),
            item_occ_clear(binToOneHot(out_cntr)),
            out_cntr(out_cntr + 1)
        ).Else(
            item_occ_clear(0)
        )
        self.dataOut(self.storage_r.r.data, exclude=[self.dataOut.data])
        self.dataOut.data(self.storage_r.r.data.data._reinterpret_cast(self.dataOut.data._dtype))
        
        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = ReorderBuffer()
    m.T = uint16_t
    m.ID_WIDTH = 4
    print(to_rtl_str(m))
        
