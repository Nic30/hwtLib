#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from itertools import chain

from hwt.math import log2ceil
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.interconnect.matrixAddrCrossbar import AxiInterconnectMatrixAddrCrossbar
from hwtSimApi.constants import CLK_PERIOD
from hwt.simulator.simTestCase import SimTestCase


class AxiInterconnectMatrixAddrCrossbar_1to1TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        u.MASTERS = ({0},)
        u.SLAVES = (
            (0x0000, 0x1000),
        )
        u.ADDR_WIDTH = log2ceil(0x1000 - 1)
        cls.compileSim(u)

    def addr_transaction(self, id_, addr, len_):
        axi_addr = self.u.m[0]
        return axi_addr._ag.create_addr_req(addr, len_, _id=id_)

    def randomize_all(self):
        u = self.u
        for i in u.s:
            self.randomize(i)

        for i in u.m:
            self.randomize(i)

        for i in u.order_m_index_for_s_data_out:
            if i is not None:
                self.randomize(i)
        for i in u.order_s_index_for_m_data_out:
            if i is not None:
                self.randomize(i)

    def test_nop(self):
        u = self.u
        self.randomize_all()

        self.runSim(10 * CLK_PERIOD)
        for i in chain(u.m, u.s):
            self.assertEmpty(i._ag.data)

        for i in u.order_m_index_for_s_data_out:
            if i is not None:
                self.assertEmpty(i._ag.data)
        for i in u.order_s_index_for_m_data_out:
            if i is not None:
                self.assertEmpty(i._ag.data)

    def test_all(self, transaction_cnt=10, magic=0):
        # :param transaction_cnt: transactions per master per connected slave
        u = self.u
        # to automatically set default addr.size
        u.DATA_WIDTH = 64
        self.randomize_all()

        slave_a_transactions = [
            [deque() for _ in u.s]
            for _ in u.m
        ]
        for master_i, (accesible_slaves, m) in enumerate(zip(u.MASTERS, u.s)):
            for slave_i, _slave_a_transacions in enumerate(slave_a_transactions):
                if slave_i not in accesible_slaves:
                    continue

                slave_a = _slave_a_transacions[master_i]
                slave_addr_offset = self.u.SLAVES[slave_i][0]
                slave_addr_mask = self.u.SLAVES[slave_i][1] - 1
                for _ in range(transaction_cnt):
                    trans = self.addr_transaction(
                        master_i, slave_addr_offset + magic, 0)
                    m._ag.data.append(trans)
                    magic += 8
                    trans = [t for t in trans]
                    trans[1] &= slave_addr_mask
                    slave_a.append(tuple(trans))

        max_trans_duration = max(len(m._ag.data) for m in u.s)
        self.runSim((40 + 4 * max_trans_duration *
                     transaction_cnt) * CLK_PERIOD)
        # assert all data was send
        for m_i, m in enumerate(u.s):
            self.assertEmpty(m._ag.data, f"master: {m_i:d}")

        for m_i, (s_for_m, accesible_slaves) in enumerate(zip(
                u.order_s_index_for_m_data_out, u.MASTERS)):
            if s_for_m is None:
                continue
            ref_s_for_m = []
            for slave_i, slave_a in enumerate(slave_a_transactions):
                if slave_i not in accesible_slaves:
                    continue

                slave_addr_offset = u.SLAVES[slave_i][0]
                for _ in range(transaction_cnt):
                    ref_s_for_m.append(slave_i)
            self.assertValSequenceEqual(
                s_for_m._ag.data, ref_s_for_m, f"master: {m_i:d}")

        # use order from u.order_m_index_for_s_data_out to rebuild original
        # order of transactions
        for s_i, (s, m_for_s, s_all_ref) in enumerate(zip(
                u.m, u.order_m_index_for_s_data_out, slave_a_transactions)):
            if m_for_s is None:
                continue
            s = s._ag.data
            m_for_s = [int(m) for m in m_for_s._ag.data]
            trans_cnt = sum([len(r) for r in s_all_ref])
            self.assertEqual(len(m_for_s), trans_cnt, f"slave: {s_i:d}")
            self.assertEqual(len(s), trans_cnt, f"slave: {s_i:d}")
            s_ref = []
            for m_i in m_for_s:
                t = s_all_ref[m_i].popleft()
                s_ref.append(t)

            self.assertValSequenceEqual(s, s_ref, f"slave: {s_i:d}")


class AxiInterconnectMatrixAddrCrossbar_1to3TC(AxiInterconnectMatrixAddrCrossbar_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        u.MASTERS = ({0, 1, 2}, )
        u.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        )
        u.ADDR_WIDTH = log2ceil(0x4000 - 1)
        cls.compileSim(u)

class AxiInterconnectMatrixAddrCrossbar_3to1TC(AxiInterconnectMatrixAddrCrossbar_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        u.MASTERS = ({0}, {0}, {0})
        u.SLAVES = (
            (0x0000, 0x1000),
        )
        u.ADDR_WIDTH = log2ceil(0x2000 - 1)
        cls.compileSim(u)


class AxiInterconnectMatrixAddrCrossbar_3to3TC(AxiInterconnectMatrixAddrCrossbar_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        #u.MASTERS = ({0, 1}, {0, 1})
        #u.SLAVES = (
        #    (0x0000, 0x1000),
        #    (0x1000, 0x1000),
        #)

        u.MASTERS = ({0, 1, 2}, {0, 1, 2}, {0, 1, 2})
        u.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        )
        u.ADDR_WIDTH = log2ceil(0x4000 - 1)
        cls.compileSim(u)


class AxiInterconnectMatrixAddrCrossbar_2to1_2to1_1toAllTC(AxiInterconnectMatrixAddrCrossbar_1to1TC):
    """
    M0,M1 -> S0
    M2,M3 -> S1
    M4    -> S0,S1
    """
    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        u.MASTERS = ({0}, {0}, {1}, {1}, {0, 1})
        u.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
        )
        u.ADDR_WIDTH = log2ceil(0x2000 - 1)
        cls.compileSim(u)


AxiInterconnectMatrixAddrCrossbar_TCs = [
    AxiInterconnectMatrixAddrCrossbar_1to1TC,
    AxiInterconnectMatrixAddrCrossbar_1to3TC,
    AxiInterconnectMatrixAddrCrossbar_3to1TC,
    AxiInterconnectMatrixAddrCrossbar_3to3TC,
    AxiInterconnectMatrixAddrCrossbar_2to1_2to1_1toAllTC
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiInterconnectMatrixAddrCrossbar_3to3TC(''))
    for tc in AxiInterconnectMatrixAddrCrossbar_TCs:
        suite.addTest(unittest.makeSuite(tc))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
