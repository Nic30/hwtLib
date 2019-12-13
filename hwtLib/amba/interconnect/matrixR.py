#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.interconnect.common import AxiInterconnectCommon
from hwtLib.amba.interconnect.matrixAddrCrossbar import AxiInterconnectMatrixAddrCrossbar
from hwtLib.amba.interconnect.matrixCrossbar import AxiInterconnectMatrixCrossbar
from hwtLib.handshaked.fifo import HandshakedFifo


class AxiInterconnectMatrixR(AxiInterconnectCommon):
    """
    Read only AXI3/4/Lite interconnect with supports transaction overlapping
    and guarantees the order order of transactions on the bus 

    :ivar order_m_index_for_s_data: list, FIFOs for each slave which keeps the information
        about which master accessed slave on this index,
        to keep the order of transactions coherent
    :ivar order_s_index_for_m_data: list, FIFOs for each master which keeps the information
        about where master should expect data

    .. hwt-schematic:: example_AxiInterconnectMatrixR
    """

    def _declr(self):
        AxiInterconnectCommon._declr(self, has_r=True, has_w=False)
        AxiInterconnectCommon._init_config_flags(self)

        if self.REQUIRED_ORDER_SYNC_M_FOR_S:
            # fifo for master index for each slave so slave knows
            # which master did read and where is should send it
            self.order_m_index_for_s_data = HObjList([
                HandshakedFifo(Handshaked) for _ in self.SLAVES])

            for f in self.order_m_index_for_s_data:
                f.DEPTH = self.MAX_TRANS_OVERLAP
                f.DATA_WIDTH = log2ceil(len(self.MASTERS))

        if self.REQUIRED_ORDER_SYNC_S_FOR_M:
            # fifo for slave index for each master
            # so master knows where it should expect the data
            self.order_s_index_for_m_data = HObjList([
                HandshakedFifo(Handshaked) for _ in self.MASTERS])

            for f in self.order_s_index_for_m_data:
                f.DEPTH = self.MAX_TRANS_OVERLAP
                f.DATA_WIDTH = log2ceil(len(self.SLAVES))

        with self._paramsShared():
            self.addr_crossbar = AxiInterconnectMatrixAddrCrossbar(
                self.intfCls.AR_CLS)

        with self._paramsShared():
            c = self.data_crossbar = AxiInterconnectMatrixCrossbar(
                self.intfCls.R_CLS)
            c.INPUT_CNT = len(self.SLAVES)
            c.OUTPUTS = self.MASTERS

    def _impl(self):
        propagateClkRstn(self)
        addr_crossbar = self.addr_crossbar
        data_crossbar = self.data_crossbar

        master_addr_channels = HObjList([m.ar for m in self.master])
        slave_addr_channels = HObjList([s.ar for s in self.slave])
        addr_crossbar.master(master_addr_channels)
        slave_addr_channels(addr_crossbar.slave)
        master_r_channels = HObjList([m.r for m in self.master])
        master_r_channels(data_crossbar.dataOut)
        slave_r_channels = HObjList([s.r for s in self.slave])
        data_crossbar.dataIn(slave_r_channels)

        if self.REQUIRED_ORDER_SYNC_S_FOR_M:
            order_s_index_for_m_data_in = HObjList([
                f.dataIn for f in self.order_s_index_for_m_data])
            order_s_index_for_m_data_in(
                addr_crossbar.order_s_index_for_m_data_out)
            order_s_index_for_m_data_out = HObjList([
                f.dataOut for f in self.order_s_index_for_m_data])
            data_crossbar.order_din_index_for_dout_in(
                order_s_index_for_m_data_out)

        if self.REQUIRED_ORDER_SYNC_M_FOR_S:
            order_m_index_for_s_data_in = HObjList([
                f.dataIn for f in self.order_m_index_for_s_data])
            order_m_index_for_s_data_in(
                addr_crossbar.order_m_index_for_s_data_out)

            order_m_index_for_s_data_out = HObjList([
                f.dataOut for f in self.order_m_index_for_s_data])
            data_crossbar.order_dout_index_for_din_in(
                order_m_index_for_s_data_out)


def example_AxiInterconnectMatrixR():
    u = AxiInterconnectMatrixR(Axi4)
    #u.MASTERS = [{0, 1}]
    #u.MASTERS = [{0, 1, 2}]
    #u.MASTERS = [{0}, {0}, {0}]
    # u.SLAVES = [(0x1000, 0x1000),
    #            (0x2000, 0x1000),
    #            (0x3000, 0x1000),
    #          ]
    #u.SLAVES = [(0x1000, 0x1000)]

    u.MASTERS = [{0, 1}, {0, 1}]
    u.SLAVES = [(0x1000, 0x1000),
                (0x2000, 0x1000),
                ]

    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = example_AxiInterconnectMatrixR()
    print(toRtl(u))
