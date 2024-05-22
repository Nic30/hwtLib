#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain
from typing import Union

from hwt.hdl.types.bitsConst import HBitsConst
from hwt.math import log2ceil
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.interconnect.matrixAddrCrossbar_test import AxiInterconnectMatrixAddrCrossbar_1to1TC
from hwtLib.amba.axi_comp.interconnect.matrixR_test import AxiInterconnectMatrixR_1to1TC
from hwtLib.amba.axi_comp.interconnect.matrixW import AxiInterconnectMatrixW
from hwtLib.amba.constants import RESP_OKAY
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class AxiInterconnectMatrixW_1to1TC(SimTestCase):
    LEN_MAX = 4

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixW(Axi4)
        dut.MASTERS = ({0}, )
        dut.SLAVES = (
            (0x0000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x1000 - 1)
        cls.compileSim(dut)

    def setUp(self):
        AxiInterconnectMatrixR_1to1TC.setUp(self)

    def randomize_all(self):
        dut = self.dut
        for i in chain(dut.s, dut.m):
            self.randomize(i)

    def test_nop(self):
        dut = self.dut
        self.randomize_all()

        self.runSim(10 * CLK_PERIOD)

        for i in chain(dut.s, dut.m):
            self.assertEmpty(i.aw._ag.data)
            self.assertEmpty(i.w._ag.data)
            self.assertEmpty(i.b._ag.data)

    def data_transaction(self, id_:int, data: Union[int, HBitsConst]):
        transactions = []
        DW = self.dut.s[0].w.DATA_WIDTH
        m = mask(DW // 8)
        for is_last, d in iter_with_last(data):
            transactions.append(
                (d, m, int(is_last))
            )
        return transactions

    def rand_write(self, master_i: int, slave_i: int, magic: int):
        """
        :ivar ~.magic: random value used to distinguis the data
        """
        m = self.memory[slave_i]
        slave_addr_offset = self.dut.SLAVES[slave_i][0]
        aw = self.dut.s[master_i].aw
        w = self.dut.s[master_i].w

        word_cnt = int(self._rand.random() * self.LEN_MAX) + 1
        in_slave_addr = m.malloc(
            word_cnt * self.dut.s[master_i].DATA_WIDTH // 8)

        data = []
        for i2 in range(word_cnt):
            data.append(magic)
            magic += i2
        indx = in_slave_addr // m.cellSize

        aw_transaction = AxiInterconnectMatrixAddrCrossbar_1to1TC.addr_transaction(
            self,
            master_i,
            slave_addr_offset + in_slave_addr,
            len(data) - 1
        )
        aw._ag.data.append(aw_transaction)
        w_transactions = self.data_transaction(master_i, data)
        w._ag.data.extend(w_transactions)
        b_transaction = (master_i, RESP_OKAY)
        return (indx, data), b_transaction

    def test_write(self, transaction_cnt=2, magic=99):
        dut = self.dut
        self.randomize_all()

        # allocate memory, prepare axi.ar transactions and store axi.r transactions
        # for later check
        slave_w_data = [[] for _ in dut.SLAVES]
        master_b_data = []
        for master_i, accesible_slaves in enumerate(dut.MASTERS):
            m_b_data = []
            master_b_data.append(m_b_data)

            for slave_i, _ in enumerate(dut.SLAVES):
                if slave_i not in accesible_slaves:
                    continue
                s_d = slave_w_data[slave_i]
                for _ in range(transaction_cnt):
                    data, b_transaction = self.rand_write(
                        master_i, slave_i, magic)
                    magic += len(data[1])
                    s_d.append(data)
                    m_b_data.append(b_transaction)

        max_trans_duration = 2 * max(len(m.aw._ag.data)
                                     for m in dut.s)\
            + max(sum(len(wt[1]) for wt in wd) for wd in slave_w_data)
        self.runSim(4 * max_trans_duration * transaction_cnt * CLK_PERIOD)

        for s_i, _w_data in enumerate(slave_w_data):
            mem = self.memory[s_i]
            for w_data in _w_data:
                offset, ref_data = w_data
                data = []
                for i in range(len(ref_data)):
                    d = mem.data.get(offset + i, None)
                    data.append(d)
                self.assertValSequenceEqual(data, ref_data)

        for m_i, (m, m_b_data) in enumerate(zip(dut.s, master_b_data)):
            self.assertValSequenceEqual(
                m.b._ag.data, m_b_data, f"master:{m_i:d}")


class AxiInterconnectMatrixW_1to3TC(AxiInterconnectMatrixW_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixW(Axi4)
        dut.MASTERS = ({0, 1, 2}, )
        dut.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x4000 - 1)
        cls.compileSim(dut)


class AxiInterconnectMatrixW_3to1TC(AxiInterconnectMatrixW_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixW(Axi4)
        dut.MASTERS = ({0}, {0}, {0})
        dut.SLAVES = (
            (0x0000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x2000 - 1)
        cls.compileSim(dut)


class AxiInterconnectMatrixW_3to3TC(AxiInterconnectMatrixW_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixW(Axi4)
        # dut.MASTERS = ({0, 1}, {0, 1})
        # dut.SLAVES = (
        #     (0x0000, 0x1000),
        #     (0x1000, 0x1000),
        # )

        dut.MASTERS = ({0, 1, 2}, {0, 1, 2}, {0, 1, 2})
        dut.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x4000 - 1)
        cls.compileSim(dut)


AxiInterconnectMatrixW_TCs = [
    AxiInterconnectMatrixW_1to1TC,
    AxiInterconnectMatrixW_1to3TC,
    AxiInterconnectMatrixW_3to1TC,
    AxiInterconnectMatrixW_3to3TC,
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiInterconnectMatrixW_1to1TC("test_write")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in AxiInterconnectMatrixW_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
