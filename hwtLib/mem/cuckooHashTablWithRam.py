#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.logic.crcPoly import CRC_32, CRC_32C
from hwtLib.mem.cuckooHashTable import CuckooHashTable
from hwtLib.mem.hashTableCoreWithRam import HashTableCoreWithRam
from hwtLib.mem.hashTable_intf import HashTableIntf


class CuckooHashTableWithRam(CuckooHashTable):
    """
    A cuckoo hash table core with integrated memory

    .. hwt-autodoc:: _example_CuckooHashTableWithRam
    """

    def __init__(self, polynomials):
        self.polynomials = polynomials
        CuckooHashTable.__init__(self)

    def _config(self):
        CuckooHashTable._config(self)
        self.TABLE_CNT = len(self.polynomials)
        self.POLYNOMIALS = Param(tuple(self.polynomials))

    def _declr(self):
        self._declr_outer_io()
        tables = HObjList(HashTableCoreWithRam(p) for p in self.polynomials)
        self.configure_tables(tables)
        self.table_cores = tables

    def _impl(self):
        self.tables_tmp = HObjList([HashTableIntf()._updateParamsFrom(t.io) for t in self.table_cores])

        for t_io, t in zip(self.tables_tmp, self.table_cores):
            t.io(t_io, exclude={t.io.lookupRes})
            t_io.lookupRes(HsBuilder(self, t.io.lookupRes).buff(latency=(1, 2)).end)

        self.tables = list(self.tables_tmp)
        CuckooHashTable._impl(self)


def _example_CuckooHashTableWithRam():
    return CuckooHashTableWithRam([CRC_32, CRC_32C])


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_CuckooHashTableWithRam()
    print(to_rtl_str(u))
