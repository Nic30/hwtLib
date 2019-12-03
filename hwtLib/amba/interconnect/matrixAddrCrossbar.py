from typing import List, Tuple

from hwt.code import log2ceil, connect, Concat, SwitchLogic, Or
from hwt.hdl.assignment import Assignment
from hwt.hdl.transTmpl import TransTmpl
from hwt.interfaces.std import Handshaked
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.interconnect.common import AxiInterconnectCommon,\
    apply_name
from hwtLib.handshaked.joinFair import HsJoinFairShare
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.oneHotToBin import oneHotToBin
from hwtLib.types.ctypes import uint8_t


class AxiInterconnectMatrixAddrCrossbar(Unit):
    """
    Component which implements N to M crossbar for AXI address channel.
    If there are multiple masters connected to any slave the access is mannaged by round-robin.

    :ivar order_s_index_for_m_data_out: handshaked interface with index of slave for each master,
        data is send on start of the transaction
    :ivar order_m_index_for_s_data_out: handshaked interface with index of master for each slave,
        data is send on start of the transaction

    .. hwt-schematic:: example_AxiInterconnectMatrixAddrCrossbar
    """

    @staticmethod
    def priorityAck(priorityReg, vldSignals, index):
        return HsJoinFairShare.priorityAck(priorityReg, vldSignals, index)

    def __init__(self, axi_addr_cls):
        self.AXI_CLS = axi_addr_cls
        super(AxiInterconnectMatrixAddrCrossbar, self).__init__()

    def _config(self):
        self.SLAVES = Param([])
        self.MASTERS = Param([])
        self.AXI_CLS._config(self)

    def _declr(self):
        AxiInterconnectCommon._declr(self, has_r=False, has_w=False)
        AxiInterconnectCommon._init_config_flags(self)

        if self.REQUIRED_ORDER_SYNC_M_FOR_S:
            # fifo for master index for each slave so slave knows
            # which master did read and where is should send it
            self.order_m_index_for_s_data_out = HObjList([
                Handshaked()._m() for _ in self.SLAVES])

            for f in self.order_m_index_for_s_data_out:
                f.DATA_WIDTH = self.MASTER_INDEX_WIDTH = log2ceil(
                    len(self.MASTERS))

        if self.REQUIRED_ORDER_SYNC_S_FOR_M:
            # fifo for slave index for each master
            # so master knows where it should expect the data
            self.order_s_index_for_m_data_out = HObjList([
                Handshaked()._m() for _ in self.MASTERS])

            for f in self.order_s_index_for_m_data_out:
                f.DATA_WIDTH = log2ceil(len(self.SLAVES))

    def propagate_addr(self, master_addr_channels, slave_addr_channels)\
            ->List[List[Tuple[RtlSignal, Assignment]]]:
        """
        :return: matrix of addr select, addr assignment for all masters and slaves
                (master X slave)
        """
        slv_en = []
        for mi, slvs in enumerate(self.MASTERS):
            _slv_en = []
            slv_en.append(_slv_en)
            srcAddrSig = master_addr_channels[mi].addr
            for si, (addr, size) in enumerate(self.SLAVES):
                dstAddrSig = slave_addr_channels[si].addr
                if si not in slvs:
                    # case where slave is not mapped to master address space
                    en = 0
                    addr_drive = dstAddrSig(None)
                else:
                    tmpl = TransTmpl(uint8_t[size], bitAddr=addr * 8)
                    # generate optimized address comparator and handle potentialy
                    # different bus address granularity
                    en, addr_drive = BusEndpoint.propagateAddr(
                        self, srcAddrSig, 8, dstAddrSig, 8, tmpl)
                _slv_en.append((en, addr_drive))

        return slv_en

    def addr_handler_1_to_1(self, master_addr_channels, slave_addr_channels):
        # 1:1, just connect the rest of the signals
        m = master_addr_channels[0]
        s = slave_addr_channels[0]
        slv_en = self.propagate_addr(master_addr_channels, slave_addr_channels)
        addr_en = slv_en[0][0][0]
        # addr already connected, valid, ready need an extra sync
        connect(m, s, exclude={m.valid, m.ready, m.addr})
        StreamNode([m], [s]).sync(addr_en)

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

            data_connect_exprs = connect(m_addr, slv_addr_tmp,
                                         exclude={m_addr.valid,
                                                  m_addr.ready,
                                                  m_addr.addr}) + [addr_assig]
            cond = m_addr.valid & isSelected
            dataCases.append((cond, data_connect_exprs))

        dataDefault = []
        for sig in slv_addr_tmp._interfaces:
            if sig not in {slv_addr_tmp.valid, slv_addr_tmp.ready}:
                dataDefault.append(sig(None))

        SwitchLogic(dataCases, dataDefault)

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
        for slv_i, (slv_addr, order_m_for_s) in enumerate(zip(
                slave_addr_channels,
                order_m_index_for_s_data_in)):

            # master.ar has valid transaction for this slave flag list
            master_vld_slave = []
            master_targets_slave = []
            for m_i, (_slv_en, m_addr) in enumerate(zip(master_to_slave_en, master_addr_channels)):
                m_addr_en_s = _slv_en[slv_i][0]
                m_targets_slave = apply_name(
                    self, m_addr_en_s, "master_%d_targets_slave_%d" % (m_i, slv_i))
                master_targets_slave.append(m_targets_slave)
                en = m_addr.valid & m_targets_slave
                master_vld_slave.append(en)

            if self.REQUIRED_ORDER_SYNC_S_FOR_M:
                # 1+ masters to 1(+) slaves
                # inject the order_s_for_m stream to a master-slv_addr_tmp
                # stream sync
                master_vld_slave = [
                    v & s_for_m.rd
                    for v, s_for_m in zip(master_vld_slave, order_s_index_for_m_data_in)
                ]

            if self.REQUIRED_ORDER_SYNC_M_FOR_S:
                # multiple masters can access the slave
                # instantiate round-robin arbiter to select master
                isSelectedFlags = HsJoinFairShare.isSelectedLogic(
                    self, master_vld_slave, slv_addr.ready, None)
                # connect handshake sync to a
                #slv_valid = Or(*isSelectedFlags) & order_m_for_s.rd
                slv_valid = Or(*[en & vld for en, vld in zip(isSelectedFlags, master_vld_slave)])\
                    & order_m_for_s.rd

                for m_i, m_ar in enumerate(master_addr_channels):
                    m_rd = ready_for_master[m_i]
                    # note: isSelectedFlags has a combinational path to a
                    # master_addr_channel.valid
                    m_rd = (
                        isSelectedFlags[m_i]
                        & master_vld_slave[m_i]
                        & slv_addr.ready
                        & order_m_for_s.rd
                    ) | m_rd
                    ready_for_master[m_i] = m_rd

                # collect info about arbitration win for slave
                slv_master_arbitration_res = [
                    isSel & vld
                    for isSel, vld in zip(isSelectedFlags, master_vld_slave)
                ]

                slv_master_arbitration_res = apply_name(
                    self, Concat(*reversed(slv_master_arbitration_res)),
                    "slave_%d_master_arbitration_res" % slv_i
                )
                order_m_for_s.vld(
                    (slv_master_arbitration_res != 0) & slv_addr.ready)
                order_m_for_s.data(oneHotToBin(
                    self, slv_master_arbitration_res))
            else:
                # valid if any master with address of this slave has valid=1
                slv_valid = Or(*master_vld_slave)

                assert order_m_for_s is None
                # only a single master can access the slave
                # if len(master_addr_channels) > 1:

                for m_i, m_en in enumerate(master_vld_slave):
                    m_rd = ready_for_master[m_i]
                    ready_for_master[m_i] = (m_en & slv_addr.ready) | m_rd
                isSelectedFlags = [1]

            slv_addr.valid(slv_valid)
            addr_assignments = [
                _slv_en[slv_i][1]
                for _slv_en in master_to_slave_en
            ]
            slv_master_arbitration_res = [
                vld & isSel & slv_addr.ready
                for isSel, vld in zip(isSelectedFlags, master_vld_slave)
            ]
            self.addr_handler_build_addr_mux(
                slv_addr,
                master_addr_channels,
                addr_assignments,
                slv_master_arbitration_res)

        for m_i, (master_addr, order_s_for_m, m_rd) in enumerate(zip(
                master_addr_channels, order_s_index_for_m_data_in, ready_for_master)):
            # collect the info about arbitration win for master
            if self.REQUIRED_ORDER_SYNC_S_FOR_M:
                slv_ens = [m[0] for m in master_to_slave_en[m_i]]
                slv_ens = oneHotToBin(self, Concat(
                    *reversed(slv_ens)), "master_%d_slv_ens" % m_i)
                order_s_for_m.data(slv_ens)
                order_s_for_m.vld(m_rd & master_addr.valid)

                m_rd = m_rd & order_s_for_m.rd

            master_addr.ready(m_rd)

    def _impl(self)->None:
        master_addr_channels = [AxiSBuilder(
            self, m).buff(1).end for m in self.master]
        slave_addr_channels = self.slave

        if self.REQUIRED_ORDER_SYNC_S_FOR_M or self.REQUIRED_ORDER_SYNC_M_FOR_S:
            if self.REQUIRED_ORDER_SYNC_S_FOR_M:
                order_s_index_for_m_data_out = self.order_s_index_for_m_data_out
            else:
                order_s_index_for_m_data_out = [None for _ in self.master]
            if self.REQUIRED_ORDER_SYNC_M_FOR_S:
                order_m_index_for_s_data_out = self.order_m_index_for_s_data_out
            else:
                order_m_index_for_s_data_out = [None for _ in self.slave]

            self.addr_handler_N_to_M(
                master_addr_channels,
                slave_addr_channels,
                order_m_index_for_s_data_out,
                order_s_index_for_m_data_out)
        else:
            self.addr_handler_1_to_1(master_addr_channels, slave_addr_channels)


def example_AxiInterconnectMatrixAddrCrossbar():
    from hwtLib.amba.axi4 import Axi4
    u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
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
    u = example_AxiInterconnectMatrixAddrCrossbar()
    print(toRtl(u))
