#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain

from hwt.math import log2ceil
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.interconnect.matrixAddrCrossbar_test import AxiInterconnectMatrixAddrCrossbar_1to1TC
from hwtLib.amba.axi_comp.interconnect.matrixCrossbar_test import AxiInterconnectMatrixCrossbar_1to1TC
from hwtLib.amba.axi_comp.interconnect.matrixR import AxiInterconnectMatrixR
from hwtLib.amba.axi_comp.sim.ram import Axi4SimRam
from hwtSimApi.constants import CLK_PERIOD


class AxiInterconnectMatrixR_1to1TC(SimTestCase):
    LEN_MAX = 4

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixR(Axi4)
        dut.MASTERS = ({0},)
        dut.SLAVES = (
            (0x0000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x1000 - 1)
        cls.compileSim(dut)

    def setUp(self):
        SimTestCase.setUp(self)
        dut = self.dut
        self.memory = [Axi4SimRam(axi=s) for s in dut.m]

    def randomize_all(self):
        dut = self.dut
        for i in chain(dut.s, dut.m):
            self.randomize(i)

    def test_nop(self):
        dut = self.dut
        self.randomize_all()

        self.runSim(10 * CLK_PERIOD)
        for i in chain(dut.s, dut.m):
            self.assertEmpty(i.ar._ag.data)
            self.assertEmpty(i.r._ag.data)

    def rand_read(self, master_i:int, slave_i:int, magic:int):
        """
        :ivar ~.magic: random value used to distinguis the data
        """
        m = self.memory[slave_i]
        slave_addr_offset = self.dut.SLAVES[slave_i][0]
        ar = self.dut.s[master_i].ar

        word_cnt = int(self._rand.random() * self.LEN_MAX) + 1
        in_slave_addr = m.malloc(
            word_cnt * self.dut.s[master_i].DATA_WIDTH // 8)
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

    def test_read(self, transaction_cnt:int=2, magic:int=99):
        dut = self.dut
        self.randomize_all()

        # allocate memory, prepare axi.ar transactions and store axi.r transactions
        # for later check
        master_r_data = []
        for master_i, accesible_slaves in enumerate(dut.MASTERS):
            m_r_data = []
            master_r_data.append(m_r_data)

            for slave_i, _ in enumerate(dut.SLAVES):
                if slave_i not in accesible_slaves:
                    continue

                for _ in range(transaction_cnt):
                    data = self.rand_read(master_i, slave_i, magic)
                    magic += len(data)
                    m_r_data.extend(data)

        max_trans_duration = max(len(m.ar._ag.data)
                                 for m in dut.s) + max(len(d) for d in master_r_data)
        self.runSim(4 * max_trans_duration * transaction_cnt * CLK_PERIOD)

        # for m_i, (m, m_r_data) in enumerate(zip(dut.saster, master_r_data)):
        #    print(len(m.r._ag.data), len(m_r_data))
        #    for _m, _m_ref in zip(m.r._ag.data, m_r_data):
        #        print(valuesToInts(_m), _m_ref)
        #    print("#############################")

        for m_i, (m, m_r_data) in enumerate(zip(dut.s, master_r_data)):
            self.assertValSequenceEqual(
                m.r._ag.data, m_r_data, f"master:{m_i:d}")


class AxiInterconnectMatrixR_1to3TC(AxiInterconnectMatrixR_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixR(Axi4)
        dut.MASTERS = ({0, 1, 2},)
        dut.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x4000 - 1)
        cls.compileSim(dut)


class AxiInterconnectMatrixR_3to1TC(AxiInterconnectMatrixR_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixR(Axi4)
        dut.MASTERS = ({0}, {0}, {0})
        dut.SLAVES = (
            (0x0000, 0x1000),
        )
        dut.ADDR_WIDTH = log2ceil(0x2000 - 1)
        cls.compileSim(dut)


class AxiInterconnectMatrixR_3to3TC(AxiInterconnectMatrixR_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixR(Axi4)
        dut.MASTERS = ({0, 1}, {0, 1})
        dut.SLAVES = (
            (0x0000, 0x1000),
            (0x1000, 0x1000),
        )

        # dut.MASTERS = ({0, 1, 2}, {0, 1, 2}, {0, 1, 2})
        # dut.SLAVES = (
        #    (0x0000, 0x1000),
        #    (0x1000, 0x1000),
        #    (0x2000, 0x1000),
        # )
        dut.ADDR_WIDTH = log2ceil(0x4000 - 1)
        cls.compileSim(dut)


AxiInterconnectMatrixR_TCs = [
    AxiInterconnectMatrixR_1to1TC,
    AxiInterconnectMatrixR_1to3TC,
    AxiInterconnectMatrixR_3to1TC,
    AxiInterconnectMatrixR_3to3TC
]

if __name__ == "__main__":
    import unittest

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiInterconnectMatrixR_1to1TC("test_read")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in AxiInterconnectMatrixR_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
