#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from itertools import chain

from hwt.math import log2ceil
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.interconnect.matrixAddrCrossbar import AxiInterconnectMatrixAddrCrossbar
from hwtSimApi.constants import CLK_PERIOD


class AxiInterconnectMatrixAddrCrossbar_1to1TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        dut.MASTERS = ({0},)
        dut.SLAVES = (
            (0x0000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x1000 - 1)
        cls.compileSim(dut)

    def addr_transaction(self, id_, addr, len_):
        axi_addr = self.dut.m[0]
        return axi_addr._ag.create_addr_req(addr, len_, _id=id_)

    def randomize_all(self):
        dut = self.dut
        for i in dut.s:
            self.randomize(i)

        for i in dut.m:
            self.randomize(i)

        for i in dut.order_m_index_for_s_data_out:
            if i is not None:
                self.randomize(i)
        for i in dut.order_s_index_for_m_data_out:
            if i is not None:
                self.randomize(i)

    def test_nop(self):
        dut = self.dut
        self.randomize_all()

        self.runSim(10 * CLK_PERIOD)
        for i in chain(dut.m, dut.s):
            self.assertEmpty(i._ag.data)

        for i in dut.order_m_index_for_s_data_out:
            if i is not None:
                self.assertEmpty(i._ag.data)
        for i in dut.order_s_index_for_m_data_out:
            if i is not None:
                self.assertEmpty(i._ag.data)

    def test_all(self, transaction_cnt=10, magic=0):
        # :param transaction_cnt: transactions per master per connected slave
        dut = self.dut
        # to automatically set default addr.size
        dut.DATA_WIDTH = 64
        self.randomize_all()

        slave_a_transactions = [
            [deque() for _ in dut.s]
            for _ in dut.m
        ]
        for master_i, (accesible_slaves, m) in enumerate(zip(dut.MASTERS, dut.s)):
            for slave_i, _slave_a_transacions in enumerate(slave_a_transactions):
                if slave_i not in accesible_slaves:
                    continue

                slave_a = _slave_a_transacions[master_i]
                slave_addr_offset = self.dut.SLAVES[slave_i][0]
                slave_addr_mask = self.dut.SLAVES[slave_i][1] - 1
                for _ in range(transaction_cnt):
                    trans = self.addr_transaction(
                        master_i, slave_addr_offset + magic, 0)
                    m._ag.data.append(trans)
                    magic += 8
                    trans = [t for t in trans]
                    trans[1] &= slave_addr_mask
                    slave_a.append(tuple(trans))

        max_trans_duration = max(len(m._ag.data) for m in dut.s)
        self.runSim((40 + 4 * max_trans_duration * 
                     transaction_cnt) * CLK_PERIOD)
        # assert all data was send
        for m_i, m in enumerate(dut.s):
            self.assertEmpty(m._ag.data, f"master: {m_i:d}")

        for m_i, (s_for_m, accesible_slaves) in enumerate(zip(
                dut.order_s_index_for_m_data_out, dut.MASTERS)):
            if s_for_m is None:
                continue
            ref_s_for_m = []
            for slave_i, slave_a in enumerate(slave_a_transactions):
                if slave_i not in accesible_slaves:
                    continue

                slave_addr_offset = dut.SLAVES[slave_i][0]
                for _ in range(transaction_cnt):
                    ref_s_for_m.append(slave_i)
            self.assertValSequenceEqual(
                s_for_m._ag.data, ref_s_for_m, f"master: {m_i:d}")

        # use order from dut.order_m_index_for_s_data_out to rebuild original
        # order of transactions
        for s_i, (s, m_for_s, s_all_ref) in enumerate(zip(
                dut.m, dut.order_m_index_for_s_data_out, slave_a_transactions)):
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
        cls.dut = dut = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        dut.MASTERS = ({0, 1, 2},)
        dut.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x4000 - 1)
        cls.compileSim(dut)


class AxiInterconnectMatrixAddrCrossbar_3to1TC(AxiInterconnectMatrixAddrCrossbar_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        dut.MASTERS = ({0}, {0}, {0})
        dut.SLAVES = (
            (0x0000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x2000 - 1)
        cls.compileSim(dut)


class AxiInterconnectMatrixAddrCrossbar_3to3TC(AxiInterconnectMatrixAddrCrossbar_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        # dut.MASTERS = ({0, 1}, {0, 1})
        # dut.SLAVES = (
        #    (0x0000, 0x1000),
        #    (0x1000, 0x1000),
        # )

        dut.MASTERS = ({0, 1, 2}, {0, 1, 2}, {0, 1, 2})
        dut.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x4000 - 1)
        cls.compileSim(dut)


class AxiInterconnectMatrixAddrCrossbar_2to1_2to1_1toAllTC(AxiInterconnectMatrixAddrCrossbar_1to1TC):
    """
    M0,M1 -> S0
    M2,M3 -> S1
    M4    -> S0,S1
    """

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        dut.MASTERS = ({0}, {0}, {1}, {1}, {0, 1})
        dut.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x2000 - 1)
        cls.compileSim(dut)


AxiInterconnectMatrixAddrCrossbar_TCs = [
    AxiInterconnectMatrixAddrCrossbar_1to1TC,
    AxiInterconnectMatrixAddrCrossbar_1to3TC,
    AxiInterconnectMatrixAddrCrossbar_3to1TC,
    AxiInterconnectMatrixAddrCrossbar_3to3TC,
    AxiInterconnectMatrixAddrCrossbar_2to1_2to1_1toAllTC
]

if __name__ == "__main__":
    import unittest

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiInterconnectMatrixAddrCrossbar_3to3TC("test_nop")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in AxiInterconnectMatrixAddrCrossbar_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
