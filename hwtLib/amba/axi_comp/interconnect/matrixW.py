#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.hObjList import HObjList
from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.utils import propagateClkRstn
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.interconnect.common import AxiInterconnectCommon
from hwtLib.amba.axi_comp.interconnect.matrixAddrCrossbar import AxiInterconnectMatrixAddrCrossbar
from hwtLib.amba.axi_comp.interconnect.matrixCrossbar import AxiInterconnectMatrixCrossbar
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.fifo import HandshakedFifo


class AxiInterconnectMatrixCrossbarB(AxiInterconnectMatrixCrossbar):

    @override
    def get_last(self, hwIO):
        return 1


class AxiInterconnectMatrixW(AxiInterconnectCommon):
    """
    Write-only AXI3/4/Lite interconnect with supports transaction overlapping
    and guarantees the order order of transactions on the bus

    .. hwt-autodoc:: example_AxiInterconnectMatrixW
    """

    @override
    def hwConfig(self):
        AxiInterconnectCommon.hwConfig(self)
        self.AW_AND_W_WORD_TOGETHER = HwParam(True)

    @override
    def hwDeclr(self):
        AxiInterconnectCommon.hwDeclr(self, has_r=False, has_w=True)
        masters_for_slave = AxiInterconnectMatrixCrossbar._masters_for_slave(
            self.MASTERS, len(self.SLAVES))

        # fifo for master index for each slave so slave knows
        # which master did read and where is should send it
        order_m_index_for_s_data: HObjList[Optional[HandshakedFifo]] = HObjList()
        order_m_index_for_s_b: HObjList[Optional[HandshakedFifo]] = HObjList()
        for connected_masters in masters_for_slave:
            if len(connected_masters) > 1:
                f_w = HandshakedFifo(HwIODataRdVld)
                f_b = HandshakedFifo(HwIODataRdVld)
                for _f in [f_w, f_b]:
                    _f.DEPTH = self.MAX_TRANS_OVERLAP
                    _f.DATA_WIDTH = log2ceil(len(self.MASTERS))
            else:
                f_w, f_b = None, None
            order_m_index_for_s_data.append(f_w)
            order_m_index_for_s_b.append(f_b)
        self.order_m_index_for_s_data = order_m_index_for_s_data
        self.order_m_index_for_s_b = order_m_index_for_s_b
        # fifo for slave index for each master
        # so master knows where it should expect the data
        order_s_index_for_m_data: HObjList[Optional[HandshakedFifo]] = HObjList()
        order_s_index_for_m_b: HObjList[Optional[HandshakedFifo]] = HObjList()
        for connected_slaves in self.MASTERS:
            if len(connected_slaves) > 1:
                f_w = HandshakedFifo(HwIODataRdVld)
                f_b = HandshakedFifo(HwIODataRdVld)

                for f in [f_w, f_b]:
                    f.DEPTH = self.MAX_TRANS_OVERLAP
                    f.DATA_WIDTH = log2ceil(len(self.SLAVES))
            else:
                f_w, f_b = None, None
            order_s_index_for_m_data.append(f_w)
            order_s_index_for_m_b.append(f_b)
        self.order_s_index_for_m_data = order_s_index_for_m_data
        self.order_s_index_for_m_b = order_s_index_for_m_b

        AXI = self.hwIOCls
        with self._hwParamsShared():
            self.addr_crossbar = AxiInterconnectMatrixAddrCrossbar(
                AXI.AW_CLS)

        with self._hwParamsShared():
            c = self.data_crossbar = AxiInterconnectMatrixCrossbar(
                AXI.W_CLS)
            c.INPUT_CNT = len(self.MASTERS)
            W_OUTPUTS = [set() for _ in self.SLAVES]
            for m_i, accessible_slaves in enumerate(self.MASTERS):
                for s_i in accessible_slaves:
                    W_OUTPUTS[s_i].add(m_i)
            c.OUTPUTS = W_OUTPUTS

        with self._hwParamsShared():
            c = self.b_crossbar = AxiInterconnectMatrixCrossbarB(
                AXI.B_CLS)
            c.INPUT_CNT = len(self.SLAVES)
            c.OUTPUTS = self.MASTERS

    @override
    def hwImpl(self):
        propagateClkRstn(self)
        addr_crossbar = self.addr_crossbar
        data_crossbar = self.data_crossbar
        b_crossbar = self.b_crossbar

        master_addr_channels = HwIOArray(m.aw for m in self.s)
        slave_addr_channels = HwIOArray(s.aw for s in self.m)
        if self.AW_AND_W_WORD_TOGETHER:
            slave_addr_channels = HwIOArray([Axi4SBuilder(self, aw, master_to_slave=False).buff(1).end
                                            for aw in slave_addr_channels])

        addr_crossbar.s(master_addr_channels)
        slave_addr_channels(addr_crossbar.m)

        master_w_channels = HwIOArray(m.w for m in self.s)
        if self.AW_AND_W_WORD_TOGETHER:
            master_w_channels = HwIOArray(Axi4SBuilder(self, w).buff(1).end
                                           for w in master_w_channels)

        data_crossbar.dataIn(master_w_channels)
        
        slave_w_channels = HwIOArray(s.w for s in self.m)
        slave_w_channels(data_crossbar.dataOut)

        master_b_channels = HwIOArray(m.b for m in self.s)
        master_b_channels(b_crossbar.dataOut)
        slave_b_channels = HwIOArray(s.b for s in self.m)
        b_crossbar.dataIn(slave_b_channels)

        for addr_crossbar_s_index_out, f_w, f_b in zip(
                addr_crossbar.order_s_index_for_m_data_out,
                self.order_s_index_for_m_data,
                self.order_s_index_for_m_b):
            if f_w is None:
                assert f_b is None
                continue
            HsBuilder(self, addr_crossbar_s_index_out)\
                .split_copy_to(f_w.dataIn, f_b.dataIn)

        for f_w, f_b, data_dout_for_din, b_din_for_dout in zip(
                self.order_s_index_for_m_data,
                self.order_s_index_for_m_b,
                data_crossbar.order_dout_index_for_din_in,
                b_crossbar.order_din_index_for_dout_in):
            if f_w is None:
                assert f_b is None
                continue
            data_dout_for_din(f_w.dataOut)
            b_din_for_dout(f_b.dataOut)

        for addr_crossbar_m_index_out, f_w, f_b in zip(
                addr_crossbar.order_m_index_for_s_data_out,
                self.order_m_index_for_s_data,
                self.order_m_index_for_s_b):
            if f_w is None:
                assert f_b is None
                assert addr_crossbar_m_index_out is None
                continue
            HsBuilder(self, addr_crossbar_m_index_out)\
                .split_copy_to(f_w.dataIn, f_b.dataIn)

        for f_w, f_b, data_din_for_dout, b_dout_for_din in zip(
                self.order_m_index_for_s_data,
                self.order_m_index_for_s_b,
                data_crossbar.order_din_index_for_dout_in,
                b_crossbar.order_dout_index_for_din_in):
            if f_w is None:
                assert f_b is None
                assert data_din_for_dout is None
                continue
            data_din_for_dout(f_w.dataOut)
            b_dout_for_din(f_b.dataOut)


def example_AxiInterconnectMatrixW():
    m = AxiInterconnectMatrixW(Axi4)
    # m.MASTERS = ({0}, )
    # m.MASTERS = ({0, 1}, )
    m.MASTERS = ({0, 1}, {0, 1})
    # m.MASTERS = ({0, 1, 2}, )
    # m.MASTERS = ({0}, {0}, {0}]
    # m.SLAVES = ((0x1000, 0x1000),
    #            (0x2000, 0x1000),
    #            (0x3000, 0x1000),
    #          )
    # m.SLAVES = ((0x1000, 0x1000), )

    # m.MASTERS = ({0, 1}, {0, 1})
    m.SLAVES = ((0x1000, 0x1000),
                (0x2000, 0x1000),
                )

    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = example_AxiInterconnectMatrixW()
    print(to_rtl_str(m))
