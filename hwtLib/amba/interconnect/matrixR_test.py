#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain

from hwt.code import log2ceil
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.interconnect.matrixAddrCrossbar_test import AxiInterconnectMatrixAddrCrossbar_1to1TC
from hwtLib.amba.interconnect.matrixCrossbar_test import AxiInterconnectMatrixCrossbar_1to1TC
from hwtLib.amba.interconnect.matrixR import AxiInterconnectMatrixR
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from pycocotb.agents.clk import DEFAULT_CLOCK


class AxiInterconnectMatrixR_1to1TC(SingleUnitSimTestCase):
    LEN_MAX = 4

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixR(Axi4)
        u.MASTERS = ({0}, )
        u.SLAVES = (
            (0x0000, 0x1000),
        )
        u.ADDR_WIDTH = log2ceil(0x1000 - 1)
        return u

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        u = self.u
        self.memory = [Axi3DenseMem(u.clk,
                                    axiAR=getattr(s, "ar", None),
                                    axiR=getattr(s, "r", None),
                                    axiAW=getattr(s, "aw", None),
                                    axiW=getattr(s, "w", None),
                                    axiB=getattr(s, "b", None),
                                    )
                       for s in u.m]

    def randomize_all(self):
        u = self.u
        for i in chain(u.s, u.m):
            self.randomize(i)

    def test_nop(self):
        u = self.u
        self.randomize_all()

        self.runSim(10 * DEFAULT_CLOCK)
        for i in chain(u.s, u.m):
            self.assertEmpty(i.ar._ag.data)
            self.assertEmpty(i.r._ag.data)

    def rand_read(self, master_i, slave_i, magic):
        """
        :ivar magic: random value used to distinguis the data
        """
        m = self.memory[slave_i]
        slave_addr_offset = self.u.SLAVES[slave_i][0]
        ar = self.u.s[master_i].ar

        word_cnt = int(self._rand.random() * self.LEN_MAX) + 1
        in_slave_addr = m.malloc(
            word_cnt * self.u.s[master_i].DATA_WIDTH // 8)
        indx = in_slave_addr // m.cellSize
        data = []

        for i2 in range(word_cnt):
            data.append(magic)
            m.data[indx + i2] = magic
            magic += i2

        id_ = 1
        ar_transaction = AxiInterconnectMatrixAddrCrossbar_1to1TC.addr_transaction(
            self,
            id_,
            slave_addr_offset + in_slave_addr,
            len(data) - 1
        )
        ar._ag.data.append(ar_transaction)
        r_transactions = AxiInterconnectMatrixCrossbar_1to1TC.data_transaction(self, id_, data)
        return r_transactions

    def test_read(self, transaction_cnt=2, magic=99):
        u = self.u
        self.randomize_all()

        # allocate memory, prepare axi.ar transactions and store axi.r transactions
        # for later check
        master_r_data = []
        for master_i, accesible_slaves in enumerate(u.MASTERS):
            m_r_data = []
            master_r_data.append(m_r_data)

            for slave_i, _ in enumerate(u.SLAVES):
                if slave_i not in accesible_slaves:
                    continue

                for _ in range(transaction_cnt):
                    data = self.rand_read(master_i, slave_i, magic)
                    magic += len(data)
                    m_r_data.extend(data)

        max_trans_duration = max(len(m.ar._ag.data)
                                 for m in u.s) + max(len(d) for d in master_r_data)
        self.runSim(4 * max_trans_duration * transaction_cnt * DEFAULT_CLOCK)

        #for m_i, (m, m_r_data) in enumerate(zip(u.saster, master_r_data)):
        #    print(len(m.r._ag.data), len(m_r_data))
        #    for _m, _m_ref in zip(m.r._ag.data, m_r_data):
        #        print(valuesToInts(_m), _m_ref)
        #    print("#############################")

        for m_i, (m, m_r_data) in enumerate(zip(u.s, master_r_data)):
            self.assertValSequenceEqual(
                m.r._ag.data, m_r_data, "master:%d" % m_i)


class AxiInterconnectMatrixR_1to3TC(AxiInterconnectMatrixR_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixR(Axi4)
        u.MASTERS = ({0, 1, 2}, )
        u.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        )
        u.ADDR_WIDTH = log2ceil(0x4000 - 1)
        return u


class AxiInterconnectMatrixR_3to1TC(AxiInterconnectMatrixR_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixR(Axi4)
        u.MASTERS = ({0}, {0}, {0})
        u.SLAVES = (
            (0x0000, 0x1000),
        )
        u.ADDR_WIDTH = log2ceil(0x2000 - 1)
        return u


class AxiInterconnectMatrixR_3to3TC(AxiInterconnectMatrixR_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixR(Axi4)
        u.MASTERS = ({0, 1}, {0, 1})
        u.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
        )

        #u.MASTERS = ({0, 1, 2}, {0, 1, 2}, {0, 1, 2})
        # u.SLAVES = (
        #    (0x0000, 0x1000),
        #    (0x1000, 0x1000),
        #    (0x2000, 0x1000),
        #)
        u.ADDR_WIDTH = log2ceil(0x4000 - 1)
        return u


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi3_rDatapumpTC('test_endstrbMultiFrame'))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixR_1to1TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixR_1to3TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixR_3to1TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixR_3to3TC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
