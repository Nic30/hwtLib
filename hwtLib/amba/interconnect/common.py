from itertools import chain
from typing import Set, List

from hwt.code import log2ceil
from hwt.hdl.constants import READ_WRITE, READ, WRITE
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.hdl.types.defs import BIT


ALL = "ALL"


class AxiInterconnectUtils():

    @classmethod
    def _normalize_master_configs(cls, MASTERS, SLAVES):
        slave_cnt = len(SLAVES)
        masters = []
        for m in MASTERS:
            if m is ALL:
                new_master_config = {
                    (i, READ_WRITE)
                    for i in range(slave_cnt)
                }
            else:
                new_master_config = set()
                for s in m:
                    if isinstance(s, int):
                        access = READ_WRITE
                    else:
                        s, access = s

                    assert s >= 0 and s < slave_cnt
                    assert access in [READ_WRITE, READ, WRITE], access

                    new_master_config.add((s, access))

            masters.append(new_master_config)

        return masters

    @classmethod
    def _assert_non_overlapping(cls, slaves):
        offset = 0
        slaves = sorted(slaves, key=lambda x: x[0])
        for addr, size in slaves:
            assert addr >= offset, (addr, size)
            offset = addr + offset

    @classmethod
    def _extract_separable_group(cls, mi: int, seen_m: Set[int],
                                 masters_connected_to: List[Set[int]],
                                 slaves_connected_to: List[Set[int]]):
        """
        Transitive enclosure of master/stalave ports on connected relation
        (Extract a group of all ports which are somehow connected to each other)
        """
        m_to_search = [mi, ]
        g_m = set()
        g_s = set()
        while m_to_search:
            mi = m_to_search.pop()
            if mi in seen_m:
                continue
            g_m.add(mi)
            seen_m.add(mi)
            slvs = masters_connected_to[mi]
            g_s.update(slvs)
            for s in slvs:
                m_to_search.extend(slaves_connected_to[s])

        if len(g_m) == 0 and len(g_s) == 0:
            return None
        else:
            return (g_m, g_s)

    @classmethod
    def _extract_separable_groups(cls, MASTERS, SLAVES, access_type):
        """
        Try to find independent subgraphs in conected master-slave ports
        on R/W channel separately
        
        :param access_type: READ or WRITE
        """
        masters_connected_to = [{_m[0] for _m in m
                                 if _m[1] == access_type or _m[1] == READ_WRITE}
                                 for m in MASTERS]
        slaves_connected_to = [set() for _ in SLAVES]
        for mi, slvs in enumerate(masters_connected_to):
            for si in slvs:
                slaves_connected_to[si].add(mi)

        #for si, mstrs in enumerate(slaves_connected_to):
        #    if not mstrs:
        #        raise AssertionError(
        #            "Slave %d can not communcate with any master" % si)
        #for mi, slvs in enumerate(slaves_connected_to):
        #    if not slvs:
        #        raise AssertionError(
        #            "Maser %d can not communcate with any master" % mi)

        seen_m = set()
        groups = []
        for mi in range(len(masters_connected_to)):
            g = cls._extract_separable_group(mi, seen_m,
                                             masters_connected_to,
                                             slaves_connected_to)
            if g is not None:
                groups.append(g)

        return groups


def apply_name(unit_instance, sig, name):
    if isinstance(sig, bool):
        t = BIT
    else:
        t = sig._dtype
    s = unit_instance._sig(name, t)
    s(sig)
    return s


class AxiInterconnectCommon(Unit):

    def __init__(self, intfCls):
        self.intfCls = intfCls
        super(AxiInterconnectCommon, self).__init__()

    def _config(self):
        self.MAX_TRANS_OVERLAP = Param(16)
        self.SLAVES = Param([])
        self.MASTERS = Param([])
        self.intfCls._config(self)

    def _init_config_flags(self):
        # flag that tells if each master should track the order of request so it
        # can collect the data in same order
        self.REQUIRED_ORDER_SYNC_S_FOR_M = len(self.SLAVES) > 1
        # flag which tells if each slave should track the origin of the request
        # so it later knows where to send the data
        self.REQUIRED_ORDER_SYNC_M_FOR_S = len(self.MASTERS) > 1

    def _declr(self, has_r=True, has_w=True):
        addClkRstn(self)
        AXI = self.intfCls
        with self._paramsShared():
            self.master = HObjList([AXI() for _ in self.MASTERS])

        with self._paramsShared(exclude=({}, {"ADDR_WIDTH"})):
            self.slave = HObjList([AXI()._m() for _ in self.SLAVES])

        for i in chain(self.master, self.slave):
            i.HAS_W = has_w
            i.HAS_R = has_r

        for s, (_, size) in zip(self.slave, self.SLAVES):
            s.ADDR_WIDTH = log2ceil(size - 1)
