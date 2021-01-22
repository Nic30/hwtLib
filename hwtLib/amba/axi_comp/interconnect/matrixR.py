#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.hObjList import HObjList
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.interconnect.common import AxiInterconnectCommon
from hwtLib.amba.axi_comp.interconnect.matrixAddrCrossbar import AxiInterconnectMatrixAddrCrossbar
from hwtLib.amba.axi_comp.interconnect.matrixCrossbar import AxiInterconnectMatrixCrossbar
from hwtLib.handshaked.fifo import HandshakedFifo


class AxiInterconnectMatrixR(AxiInterconnectCommon):
    """
    Read only AXI3/4/Lite interconnect with supports transaction overlapping
    and guarantees the order order of transactions on the bus

    :ivar ~.order_m_index_for_s_data: list, FIFOs for each slave which keeps the information
        about which master accessed slave on this index,
        to keep the order of transactions coherent
    :ivar ~.order_s_index_for_m_data: list, FIFOs for each master which keeps the information
        about where master should expect data

    .. hwt-autodoc:: example_AxiInterconnectMatrixR
    """

    def _declr(self):
        AxiInterconnectCommon._declr(self, has_r=True, has_w=False)
        masters_for_slave = AxiInterconnectMatrixCrossbar._masters_for_slave(
            self.MASTERS, len(self.SLAVES))

        # fifo for master index for each slave so slave knows
        # which master did read and where is should send it
        order_m_index_for_s_data = HObjList()
        for connected_masters in masters_for_slave:
            if len(connected_masters) > 1:
                f = HandshakedFifo(Handshaked)
                f.DEPTH = self.MAX_TRANS_OVERLAP
                f.DATA_WIDTH = log2ceil(len(self.MASTERS))
            else:
                f = None
            order_m_index_for_s_data.append(f)
        self.order_m_index_for_s_data = order_m_index_for_s_data
        # fifo for slave index for each master
        # so master knows where it should expect the data
        order_s_index_for_m_data = HObjList()
        for connected_slaves in self.MASTERS:
            if len(connected_slaves) > 1:
                f = HandshakedFifo(Handshaked)
                f.DEPTH = self.MAX_TRANS_OVERLAP
                f.DATA_WIDTH = log2ceil(len(self.SLAVES))
            else:
                f = None
            order_s_index_for_m_data.append(f)
        self.order_s_index_for_m_data = order_s_index_for_m_data

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

        master_addr_channels = HObjList([m.ar for m in self.s])
        slave_addr_channels = HObjList([s.ar for s in self.m])
        addr_crossbar.s(master_addr_channels)
        slave_addr_channels(addr_crossbar.m)
        master_r_channels = HObjList([m.r for m in self.s])
        master_r_channels(data_crossbar.dataOut)
        slave_r_channels = HObjList([s.r for s in self.m])
        data_crossbar.dataIn(slave_r_channels)

        for m_i, f in enumerate(self.order_s_index_for_m_data):
            if f is None:
                continue
            f.dataIn(addr_crossbar.order_s_index_for_m_data_out[m_i])
            data_crossbar.order_din_index_for_dout_in[m_i](f.dataOut)

        for s_i, f in enumerate(self.order_m_index_for_s_data):
            if f is None:
                continue
            f.dataIn(addr_crossbar.order_m_index_for_s_data_out[s_i])
            data_crossbar.order_dout_index_for_din_in[s_i](f.dataOut)


def example_AxiInterconnectMatrixR():
    u = AxiInterconnectMatrixR(Axi4)
    # u.MASTERS = ({0, 1}, )
    # u.MASTERS = ({0, 1, 2}, )
    # u.MASTERS = ({0}, {0}, {0}, )
    # u.SLAVES = ((0x1000, 0x1000),
    #            (0x2000, 0x1000),
    #            (0x3000, 0x1000),
    #          )
    # u.SLAVES = ((0x1000, 0x1000))

    u.MASTERS = ({0, 1}, {0, 1})
    u.SLAVES = ((0x1000, 0x1000),
                (0x2000, 0x1000),
                )

    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = example_AxiInterconnectMatrixR()
    print(to_rtl_str(u))
