#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Tuple

from hwt.code import Concat, SwitchLogic, Or
from hwt.code_utils import rename_signal
from hwt.hdl.statements.assignmentContainer import HdlAssignmentContainer
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.defs import BIT
from hwt.interfaces.std import Handshaked
from hwt.math import log2ceil
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.amba.axi_comp.interconnect.common import AxiInterconnectCommon
from hwtLib.amba.axi_comp.interconnect.matrixCrossbar import AxiInterconnectMatrixCrossbar
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.handshaked.joinFair import HsJoinFairShare
from hwtLib.logic.oneHotToBin import oneHotToBin
from hwtLib.types.ctypes import uint8_t


class AxiInterconnectMatrixAddrCrossbar(Unit):
    """
    Component which implements N to M crossbar for AXI address channel.
    If there are multiple masters connected to any slave the access is mannaged by round-robin.

    :ivar ~.order_s_index_for_m_data_out: handshaked interface with index of slave for each master,
        data is send on start of the transaction
    :ivar ~.order_m_index_for_s_data_out: handshaked interface with index of master for each slave,
        data is send on start of the transaction

    .. hwt-autodoc:: example_AxiInterconnectMatrixAddrCrossbar
    """

    @staticmethod
    def priorityAck(priorityReg, vldSignals, index):
        return HsJoinFairShare.priorityAck(priorityReg, vldSignals, index)

    def __init__(self, axi_addr_cls):
        self.intfCls = axi_addr_cls
        super(AxiInterconnectMatrixAddrCrossbar, self).__init__()

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.SLAVES = Param(tuple())
        self.MASTERS = Param(tuple())
        self.intfCls._config(self)

    def _declr(self):
        AxiInterconnectCommon._declr(self, has_r=False, has_w=False)
        self.MASTERS_FOR_SLAVE = AxiInterconnectMatrixCrossbar._masters_for_slave(
            self.MASTERS, len(self.SLAVES))
        MASTER_INDEX_WIDTH = log2ceil(len(self.MASTERS))
        SLAVE_INDEX_WIDTH = log2ceil(len(self.SLAVES))

        # fifo for master index for each slave so slave knows
        # which master did read and where is should send it
        order_m_index_for_s_data_out = HObjList()
        for connected_masters in self.MASTERS_FOR_SLAVE:
            if len(connected_masters) > 1:
                f = Handshaked()._m()
                f.DATA_WIDTH = MASTER_INDEX_WIDTH
            else:
                f = None
            order_m_index_for_s_data_out.append(f)
        self.order_m_index_for_s_data_out = order_m_index_for_s_data_out

        order_s_index_for_m_data_out = HObjList()
        for slaves in self.MASTERS:
            # fifo for slave index for each master
            # so master knows where it should expect the data
            if len(slaves) > 1:
                f = Handshaked()._m()
                f.DATA_WIDTH = SLAVE_INDEX_WIDTH
            else:
                f = None
            order_s_index_for_m_data_out.append(f)
        self.order_s_index_for_m_data_out = order_s_index_for_m_data_out

    def propagate_addr(self, master_addr_channels, slave_addr_channels)\
            ->List[List[Tuple[RtlSignal, HdlAssignmentContainer]]]:
        """
        :return: matrix of tuple(addr select, addr assignment) for all masters and slaves
                (master X slave)
        """
        slv_en = []
        for mi, connected_slaves in enumerate(self.MASTERS):
            _slv_en = []
            slv_en.append(_slv_en)
            srcAddrSig = master_addr_channels[mi].addr
            for s_i, (addr, size) in enumerate(self.SLAVES):
                dstAddrSig = slave_addr_channels[s_i].addr
                if s_i not in connected_slaves:
                    # case where slave is not mapped to master address space
                    en = BIT.from_py(0)
                    addr_drive = None
                else:
                    tmpl = TransTmpl(uint8_t[size], bitAddr=addr * 8)
                    # generate optimized address comparator and handle potentially
                    # different bus address granularity
                    en, addr_drive = BusEndpoint.propagateAddr(
                        self, srcAddrSig, 8, dstAddrSig, 8, tmpl)
                _slv_en.append((en, addr_drive))

        return slv_en

    def addr_handler_build_addr_mux(self,
                                    slv_addr_tmp, master_addr_channels,
                                    addr_assignments, isSelectedFlags):
        """
        build all master addr to this slave mux
        """
        dataCases = []
        # for each connected master
        for isSelected, m_addr, addr_assig in zip(isSelectedFlags,
                                                  master_addr_channels,
                                                  addr_assignments):
            if addr_assig is None:
                continue
            data_connect_exprs = slv_addr_tmp(m_addr,
                                         exclude={m_addr.valid,
                                                  m_addr.ready,
                                                  m_addr.addr}) + [addr_assig]
            cond = m_addr.valid & isSelected
            dataCases.append((cond, data_connect_exprs))

        dataDefault = []
        for sig in slv_addr_tmp._interfaces:
            if sig not in {slv_addr_tmp.valid, slv_addr_tmp.ready}:
                dataDefault.append(sig(None))

        return SwitchLogic(dataCases, dataDefault)

    def addr_handler_N_to_M(self, master_addr_channels, slave_addr_channels,
                            order_m_index_for_s_data_in,
                            order_s_index_for_m_data_in):
        """
        for each slave use roundrobin to select the master
        and store indexes of master and slave for later use
        """
        # create all connections on address signal to a temporary interfaces
        # and resolve enable signals
        master_to_slave_en = self.propagate_addr(
            master_addr_channels, slave_addr_channels)
        ready_for_master = [0 for _ in master_addr_channels]

        # for each slave
        for slv_i, (slv_addr, order_m_for_s, connected_masters) in enumerate(zip(
                slave_addr_channels,
                order_m_index_for_s_data_in,
                self.MASTERS_FOR_SLAVE)):

            # master.ar has valid transaction for this slave flag list
            master_vld_slave = []
            master_targets_slave = []
            for m_i, (_slv_en, m_addr) in enumerate(zip(master_to_slave_en, master_addr_channels)):
                if m_i in connected_masters:
                    m_addr_en_s = _slv_en[slv_i][0]
                    m_targets_slave = rename_signal(
                        self, m_addr_en_s, f"master_{m_i:d}_targets_slave_{slv_i:d}")
                    master_targets_slave.append(m_targets_slave)
                    en = m_addr.valid & m_targets_slave
                else:
                    en = BIT.from_py(0)
                master_vld_slave.append(en)

            # 1+ masters to 1(+) slaves
            # inject the order_s_for_m stream to a master-slv_addr_tmp
            # stream sync
            master_vld_slave = [
                v if s_for_m is None else v & s_for_m.rd
                for v, s_for_m in zip(master_vld_slave, order_s_index_for_m_data_in)
            ]

            # multiple masters can access the slave
            # instantiate round-robin arbiter to select master
            isSelectedFlags = HsJoinFairShare.isSelectedLogic(
                self, master_vld_slave, slv_addr.ready, None)

            slv_valid = []
            for m_i, (en, vld) in enumerate(zip(isSelectedFlags, master_vld_slave)):
                if m_i in connected_masters:
                    _en = en & vld
                    slv_valid.append(_en)
            slv_valid = Or(*slv_valid)
            if order_m_for_s is not None:
                slv_valid = slv_valid & order_m_for_s.rd
            slv_addr.valid(slv_valid)

            for m_i, slaves_for_master in enumerate(self.MASTERS):
                if slv_i in slaves_for_master:
                    m_rd = ready_for_master[m_i]
                    # note: isSelectedFlags has a combinational path to a
                    # master_addr_channel.valid
                    m_rd_from_this_s = (
                        isSelectedFlags[m_i]
                        & master_vld_slave[m_i]
                        & slv_addr.ready
                    )
                    if order_m_for_s is not None:
                        m_rd_from_this_s = m_rd_from_this_s & order_m_for_s.rd
                    ready_for_master[m_i] = m_rd_from_this_s | m_rd

            # collect info about arbitration win for slave
            slv_master_arbitration_res = []
            for m_i, (isSel, vld) in enumerate(zip(isSelectedFlags,
                                                   master_vld_slave)):
                if m_i in connected_masters:
                    ar = isSel & vld
                else:
                    assert not vld, vld
                    ar = BIT.from_py(0)
                slv_master_arbitration_res.append(ar)

            slv_master_arbitration_res = rename_signal(
                self, Concat(*reversed(slv_master_arbitration_res)),
                f"slave_{slv_i}_master_arbitration_res"
            )
            if order_m_for_s is not None:
                order_m_for_s.vld(
                    (slv_master_arbitration_res != 0) & slv_addr.ready)
                order_m_for_s.data(oneHotToBin(
                    self, slv_master_arbitration_res))

            slv_master_arbitration_res = [
                vld & isSel & slv_addr.ready
                for isSel, vld in zip(isSelectedFlags, master_vld_slave)
            ]
            addr_assignments = [
                _slv_en[slv_i][1]
                for _slv_en in master_to_slave_en
            ]
            self.addr_handler_build_addr_mux(
                slv_addr,
                master_addr_channels,
                addr_assignments,
                slv_master_arbitration_res)

        for m_i, (master_addr, order_s_for_m, m_rd, connected_slaves) in enumerate(zip(
                master_addr_channels,
                order_s_index_for_m_data_in,
                ready_for_master,
                self.MASTERS)):
            # collect the info about arbitration win for master
            if len(connected_slaves) > 1:
                slv_ens = [m[0] for m in master_to_slave_en[m_i]]
                slv_ens = oneHotToBin(self, Concat(
                    *reversed(slv_ens)), f"master_{m_i:d}_slv_ens")
                order_s_for_m.data(slv_ens)
                order_s_for_m.vld(m_rd & master_addr.valid)

                m_rd = m_rd & order_s_for_m.rd

            master_addr.ready(m_rd)

    def _impl(self):
        master_addr_channels = [
            AxiSBuilder(self, m).buff(1).end
            for m in self.s]
        slave_addr_channels = self.m

        order_s_index_for_m_data_out = self.order_s_index_for_m_data_out
        order_m_index_for_s_data_out = self.order_m_index_for_s_data_out

        self.addr_handler_N_to_M(
            master_addr_channels,
            slave_addr_channels,
            order_m_index_for_s_data_out,
            order_s_index_for_m_data_out)


def example_AxiInterconnectMatrixAddrCrossbar():
    from hwtLib.amba.axi4 import Axi4
    u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
    # u.MASTERS = ({0, 1},)
    # u.MASTERS = ({0, 1, 2},)
    # u.MASTERS = ({0}, {0}, {0})
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
    u = example_AxiInterconnectMatrixAddrCrossbar()
    print(to_rtl_str(u))
