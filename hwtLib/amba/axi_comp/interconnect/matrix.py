#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Set, List, Tuple

from hwt.hdl.constants import READ, READ_WRITE, WRITE
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwtLib.abstract.busInterconnect import BusInterconnectUtils, \
    BusInterconnect
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.interconnect.common import AxiInterconnectCommon
from hwtLib.amba.axi_comp.interconnect.matrixR import AxiInterconnectMatrixR
from hwtLib.amba.axi_comp.interconnect.matrixW import AxiInterconnectMatrixW
from ipCorePackager.constants import INTF_DIRECTION


class AxiInterconnectMatrix(AxiInterconnectCommon):
    """
    Matrix style interconnect for AXI-3/4/Lite interfaces

    :ivar ~.SLAVES: list of configuration of slave interfaces,
        configuration is tuple (address, size)
    :ivar ~.MASTERS: list of configuration of master interfaces,
        configuration is ALL if the master has visibility to all slaves
        or tuple of flags, where True means the master has visibility to slave
        on this index

    :note: s[x] port should be connected to a AXI master,
           m[x] port should be connected to outside AXI slave

    .. hwt-autodoc:: example_AxiInterconnectMatrix
    """

    def configure_sub_interconnect(self,
                                   master_indexes: Set[int],
                                   slave_indexes: Set[int],
                                   sub_interconnect: Union[AxiInterconnectMatrixR,
                                                           AxiInterconnectMatrixW]
                                   ) -> List[Tuple[AxiInterconnectCommon, INTF_DIRECTION, int, int]]:
        """
        :note: sub interconnect are used if there are distinct group of masters and slaves in order
            to avoid unnecessary logic
        :return: tuples (sub_interconnect, SLAVE/MASTER,
            index of interface on this component, index of interface on sub_interconnect)
        """
        assert master_indexes
        assert slave_indexes
        connected_slaves_per_master = []
        all_used_slaves = set()
        for m_i in master_indexes:
            _m = self.MASTERS[m_i]
            slvs = {s_i for s_i, _ in _m if s_i in slave_indexes}
            connected_slaves_per_master.append(slvs)
            all_used_slaves.update(slvs)

        assert all_used_slaves
        # remove the empty intervals in slave indexing
        all_used_slaves = sorted(all_used_slaves)
        slv_index_map = {s_i: new_s_i for new_s_i,
                         s_i in enumerate(all_used_slaves)}
        if len(all_used_slaves) - 1 != all_used_slaves[-1]:
            connected_slaves_per_master = [
                {slv_index_map[s] for s in slvs}
                for slvs in connected_slaves_per_master
            ]

        sub_interconnect.MASTERS = tuple(connected_slaves_per_master)
        sub_interconnect.SLAVES = tuple(self.SLAVES[s_i] for s_i in slave_indexes)

        # build connection informations for later use
        sub_interconnect_connetions = []
        for sub_m_i, m_i in enumerate(sorted(master_indexes)):
            c = (sub_interconnect, INTF_DIRECTION.MASTER, m_i, sub_m_i)
            sub_interconnect_connetions.append(c)
        for sub_s_i, s_i in enumerate(all_used_slaves):
            c = (sub_interconnect, INTF_DIRECTION.SLAVE, s_i, sub_s_i)
            sub_interconnect_connetions.append(c)

        return sub_interconnect_connetions

    def _config(self):
        AxiInterconnectCommon._config(self)

    def _declr(self):
        BusInterconnect._normalize_config(self)
        self.connection_groups_r = BusInterconnectUtils._extract_separable_groups(
            self.MASTERS, self.SLAVES, READ)
        self.connection_groups_w = BusInterconnectUtils._extract_separable_groups(
            self.MASTERS, self.SLAVES, WRITE)
        super(AxiInterconnectMatrix, self)._declr()

        # instantiate sub interconnects for each independent master-slave connection
        # subgraph (r, w separately)
        self.sub_interconnect_connections = []
        r_interconnects = HObjList()
        masters_with_read_ch = set()
        slaves_with_read_ch = set()
        for r_group in self.connection_groups_r:
            master_indexes, slave_indexes = r_group
            masters_with_read_ch.update(master_indexes)
            slaves_with_read_ch.update(slave_indexes)

            inter = AxiInterconnectMatrixR(self.intfCls)
            con = self.configure_sub_interconnect(
                master_indexes, slave_indexes, inter)
            r_interconnects.append(inter)
            self.sub_interconnect_connections.extend(con)

        masters_with_write_ch = set()
        slaves_with_write_ch = set()
        w_interconnects = HObjList()
        for w_group in self.connection_groups_w:
            master_indexes, slave_indexes = w_group
            masters_with_write_ch.update(master_indexes)
            slaves_with_write_ch.update(slave_indexes)

            inter = AxiInterconnectMatrixW(self.intfCls)
            con = self.configure_sub_interconnect(
                master_indexes, slave_indexes, inter)
            w_interconnects.append(inter)
            self.sub_interconnect_connections.extend(con)

        with self._paramsShared(exclude=({"SLAVES", "MASTERS"}, set())):
            self.r_interconnects = r_interconnects
            self.w_interconnects = w_interconnects

        # dissable read/write unused channels on master/slave interfaces
        for m_i, m in enumerate(self.s):
            m.HAS_R = m_i in masters_with_read_ch
            m.HAS_W = m_i in masters_with_write_ch
            assert m.HAS_R or m.HAS_W, m_i

        for s_i, s in enumerate(self.m):
            s.HAS_R = s_i in slaves_with_read_ch
            s.HAS_W = s_i in slaves_with_write_ch
            assert s.HAS_R or s.HAS_W, s_i

    def _impl(self):
        propagateClkRstn(self)
        for sub_interconnect, m_or_s, i, sub_i in self.sub_interconnect_connections:
            is_r = isinstance(sub_interconnect, AxiInterconnectMatrixR)
            if not is_r:
                assert isinstance(sub_interconnect, AxiInterconnectMatrixW)

            if m_or_s == INTF_DIRECTION.MASTER:
                m_axi = self.s[i]
                s_axi = sub_interconnect.s[sub_i]
            else:
                assert m_or_s == INTF_DIRECTION.SLAVE, m_or_s
                s_axi = self.m[i]
                m_axi = sub_interconnect.m[sub_i]

            if is_r:
                s_axi.ar(m_axi.ar)
                m_axi.r(s_axi.r)
            else:
                s_axi.aw(m_axi.aw)
                s_axi.w(m_axi.w)
                m_axi.b(s_axi.b)


def example_AxiInterconnectMatrix():
    u = AxiInterconnectMatrix(Axi4)
    u.MASTERS = ({(0, READ), (1, READ_WRITE)},
                 )
    u.SLAVES = ((0x1000, 0x1000),
                (0x2000, 0x1000))
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = example_AxiInterconnectMatrix()
    print(to_rtl_str(u))
