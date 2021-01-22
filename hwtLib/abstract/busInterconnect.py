from typing import List, Set

from hwt.hdl.constants import READ, WRITE, READ_WRITE
from hwt.math import log2ceil, isPow2
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class AUTO_ADDR():
    """constant which means that address should be picked automatically"""
    pass


"""
:var ALL: constant used to specify that master connected to interconnect has visibility to all slaves
"""
ALL = "ALL"


class BusInterconnectUtils():

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

                    assert s >= 0 and s < slave_cnt, (s, slave_cnt)
                    assert access in [READ_WRITE, READ, WRITE], access

                    new_master_config.add((s, access))

            masters.append(new_master_config)

        return tuple(masters)

    def _normalize_slave_configs(self, SLAVES, data_width=None):
        if data_width is None:
            data_width = self.DATA_WIDTH
        _slaves = []
        maxAddr = 0
        for address, size in SLAVES:
            if not isPow2(size):
                # it is not possible to just use prefix bits to select a destination
                raise AssertionError(
                    "Size which is not power of 2 is suboptimal for interconnects")

            if address == AUTO_ADDR:
                address = maxAddr
                isAligned = (address % size) == 0
                if not isAligned:
                    address = ((address // size) + 1) * size
            else:
                isAligned = (address % size) == 0
                if not isAligned:
                    raise AssertionError(
                        f"Offset which is not aligned to size is suboptimal 0x{address:x} 0x{size:x}")

            maxAddr = max(maxAddr, address + size)
            _slaves.append((address, size))

        self._slaves = sorted(_slaves, key=lambda x: x[0])

        # check for address space colisions
        lastAddr = -1
        for addr, size in self._slaves:
            if lastAddr >= addr:
                raise ValueError(
                    f"Address space on address 0x{addr:x} colliding with previous")
            lastAddr = addr + size - 1
        return _slaves

    @classmethod
    def _assert_non_overlapping(cls, slaves):
        offset = 0
        slaves = sorted(slaves, key=lambda x: x[0])
        for addr, size in slaves:
            assert addr >= offset, (addr, size)
            offset = addr + size

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
        #            f"Slave {si:d} can not communcate with any master")
        #for mi, slvs in enumerate(slaves_connected_to):
        #    if not slvs:
        #        raise AssertionError(
        #            "Maser {mi:d} can not communcate with any master")

        seen_m = set()
        groups = []
        for mi in range(len(masters_connected_to)):
            g = cls._extract_separable_group(mi, seen_m,
                                             masters_connected_to,
                                             slaves_connected_to)
            if g is not None:
                groups.append(g)

        return groups


class BusInterconnect(Unit):
    """
    Abstract class of bus interconnects

    :ivar ~.m: HObjList of master interfaces
    :ivar ~.s: HObjList of slave interfaces
    """

    def _config(self):
        self.SLAVES = Param(tuple())
        self.MASTERS = Param(tuple())
        self._config_normalized = False

    def _normalize_config(self):
        if self._config_normalized:
            return
        self.SLAVES = BusInterconnectUtils._normalize_slave_configs(
            self, self.SLAVES)
        BusInterconnectUtils._assert_non_overlapping(self.SLAVES)
        self.MASTERS = BusInterconnectUtils._normalize_master_configs(
            self.MASTERS, self.SLAVES)
        self._config_normalized = True

    def getOptimalAddrSize(self):
        if not self._config_normalized:
            self._normalize_config()
        last = self.SLAVES[-1]
        maxAddr = last[0] + last[1]
        maxAddr -= self.DATA_WIDTH // 8
        assert maxAddr >= 0
        return log2ceil(maxAddr)
