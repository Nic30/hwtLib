#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain

from hwt.code import log2ceil
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.amba.interconnect.matrixAddrCrossbar_test import AxiInterconnectMatrixAddrCrossbar_1to1TC
from hwtLib.amba.interconnect.matrixW import AxiInterconnectMatrixW
from pyMathBitPrecise.bit_utils import mask
from pycocotb.agents.clk import DEFAULT_CLOCK
from hwtLib.amba.interconnect.matrixR_test import AxiInterconnectMatrixR_1to1TC


class AxiInterconnectMatrixW_1to1TC(SingleUnitSimTestCase):
    LEN_MAX = 4

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixW(Axi4)
        u.MASTERS = [{0}]
        u.SLAVES = [
            (0x0000, 0x1000),
        ]
        u.ADDR_WIDTH = log2ceil(0x1000 - 1)
        return u

    def setUp(self):
        AxiInterconnectMatrixR_1to1TC.setUp(self)

    def randomize_all(self):
        u = self.u
        for i in chain(u.master, u.slave):
            self.randomize(i)

    def test_nop(self):
        u = self.u
        self.randomize_all()

        self.runSim(10 * DEFAULT_CLOCK)

        for i in chain(u.master, u.slave):
            self.assertEmpty(i.aw._ag.data)
            self.assertEmpty(i.w._ag.data)
            self.assertEmpty(i.b._ag.data)

    def data_transaction(self, id_, data):
        transactions = []
        DW = self.u.master[0].w.DATA_WIDTH
        for is_last, d in iter_with_last(data):
            transactions.append(
                (d, mask(DW // 8), int(is_last))
            )
        return transactions

    def rand_write(self, master_i, slave_i, magic):
        """
        :ivar magic: random value used to distinguis the data
        """
        m = self.memory[slave_i]
        slave_addr_offset = self.u.SLAVES[slave_i][0]
        aw = self.u.master[master_i].aw
        w = self.u.master[master_i].w

        word_cnt = int(self._rand.random() * self.LEN_MAX) + 1
        in_slave_addr = m.malloc(
            word_cnt * self.u.master[master_i].DATA_WIDTH // 8)

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
        u = self.u
        self.randomize_all()

        # allocate memory, prepare axi.ar transactions and store axi.r transactions
        # for later check
        slave_w_data = [[] for _ in u.SLAVES]
        master_b_data = []
        for master_i, accesible_slaves in enumerate(u.MASTERS):
            m_b_data = []
            master_b_data.append(m_b_data)

            for slave_i, _ in enumerate(u.SLAVES):
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
                                     for m in u.master)\
            + max(sum(len(wt[1]) for wt in wd) for wd in slave_w_data)
        self.runSim(4 * max_trans_duration * transaction_cnt * DEFAULT_CLOCK)

        for s_i, _w_data in enumerate(slave_w_data):
            mem = self.memory[s_i]
            for w_data in _w_data:
                offset, ref_data = w_data
                data = []
                for i in range(len(ref_data)):
                    d = mem.data.get(offset + i, None)
                    data.append(d)
                self.assertValSequenceEqual(data, ref_data)

        for m_i, (m, m_b_data) in enumerate(zip(u.master, master_b_data)):
            self.assertValSequenceEqual(
                m.b._ag.data, m_b_data, "master:%d" % m_i)


class AxiInterconnectMatrixW_1to3TC(AxiInterconnectMatrixW_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixW(Axi4)
        u.MASTERS = [{0, 1, 2}]
        u.SLAVES = [
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        ]
        u.ADDR_WIDTH = log2ceil(0x4000 - 1)
        return u


class AxiInterconnectMatrixW_3to1TC(AxiInterconnectMatrixW_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixW(Axi4)
        u.MASTERS = [{0}, {0}, {0}]
        u.SLAVES = [
            (0x0000, 0x1000),
        ]
        u.ADDR_WIDTH = log2ceil(0x2000 - 1)
        return u


class AxiInterconnectMatrixW_3to3TC(AxiInterconnectMatrixW_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixW(Axi4)
        # u.MASTERS = [{0, 1}, {0, 1}]
        # u.SLAVES = [
        #     (0x0000, 0x1000),
        #     (0x1000, 0x1000),
        # ]

        u.MASTERS = [{0, 1, 2}, {0, 1, 2}, {0, 1, 2}]
        u.SLAVES = [
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        ]
        u.ADDR_WIDTH = log2ceil(0x4000 - 1)
        return u


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi3_rDatapumpTC('test_endstrbMultiFrame'))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixW_1to1TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixW_1to3TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixW_3to1TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixW_3to3TC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
