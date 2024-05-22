#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain

from hwt.math import log2ceil
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.interconnect.matrixCrossbar import AxiInterconnectMatrixCrossbar
from hwtLib.amba.constants import RESP_OKAY
from hwtSimApi.constants import CLK_PERIOD


class AxiInterconnectMatrixCrossbar_1to1TC(SimTestCase):
    LEN_MAX = 4

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixCrossbar(Axi4.R_CLS)
        dut.OUTPUTS = [{0}]
        dut.INPUT_CNT = 1
        cls.compileSim(dut)

    def data_transaction(self, id_, data):
        r_transactions = []
        for is_last, d in iter_with_last(data):
            r_transactions.append(
                (id_, d, RESP_OKAY, int(is_last))
            )
        return r_transactions

    def rand_transaction(self, magic, input_i, output_i, expected_outputs):
        dut = self.dut
        word_cnt = int(self._rand.random() * self.LEN_MAX) + 1
        data = [magic + i for i in range(word_cnt)]
        data = self.data_transaction(input_i, data)
        dut.dataIn[input_i]._ag.data.extend(data)

        hwIO = dut.order_dout_index_for_din_in[input_i]
        if hwIO is not None:
            hwIO._ag.data.append(output_i)

        hwIO = dut.order_din_index_for_dout_in[output_i]
        if hwIO is not None:
            hwIO._ag.data.append(input_i)

        expected_outputs[output_i].extend(data)
        return magic + word_cnt

    def randomize_all(self):
        dut = self.dut
        for i in dut.dataOut:
            self.randomize(i)

        for i in dut.dataIn:
            self.randomize(i)

        for i in dut.order_dout_index_for_din_in:
            if i is not None:
                self.randomize(i)
        for i in dut.order_din_index_for_dout_in:
            if i is not None:
                self.randomize(i)

    def test_nop(self):
        dut = self.dut
        self.randomize_all()

        self.runSim(10 * CLK_PERIOD)
        for i in chain(dut.dataIn, dut.dataOut):
            self.assertEmpty(i._ag.data)

        for i in dut.order_dout_index_for_din_in:
            if i is not None:
                self.assertEmpty(i._ag.data)

        for i in dut.order_din_index_for_dout_in:
            if i is not None:
                self.assertEmpty(i._ag.data)

    def test_all(self, transaction_cnt=10, magic=0):
        # :param transaction_cnt: transactions per master per connected slave
        dut = self.dut
        # self.randomize_all()

        expected_transactions = [[] for _ in dut.dataOut]
        for output_i, accesible_inputs in enumerate(dut.OUTPUTS):
            for input_i, _ in enumerate(dut.dataIn):
                if input_i not in accesible_inputs:
                    continue
                for _ in range(transaction_cnt):
                    magic = self.rand_transaction(
                        magic, input_i, output_i, expected_transactions)

        max_trans_duration = max(len(dout) for dout in expected_transactions)
        self.runSim((500 + 5 * max_trans_duration * 
                     transaction_cnt) * CLK_PERIOD)
        # assert all data was send
        for m_i, din in enumerate(dut.dataIn):
            self.assertEmpty(din._ag.data, f"dataIn: {m_i:d}")

        # check the address transactions arrived correctly on slave
        for dout_i, (dout, dout_ref) in enumerate(zip(
                dut.dataOut, expected_transactions)):
            dout = dout._ag.data
            self.assertValSequenceEqual(dout, dout_ref, f"dataOut: {dout_i:d}")


class AxiInterconnectMatrixCrossbar_1to3TC(AxiInterconnectMatrixCrossbar_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixCrossbar(Axi4.R_CLS)
        dut.OUTPUTS = [{0, 1, 2}]
        dut.INPUT_CNT = 3
        cls.compileSim(dut)


class AxiInterconnectMatrixCrossbar_3to1TC(AxiInterconnectMatrixCrossbar_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixCrossbar(Axi4.R_CLS)
        dut.OUTPUTS = [{0}, {0}, {0}]
        dut.INPUT_CNT = 1
        dut.ADDR_WIDTH = log2ceil(0x2000 - 1)
        cls.compileSim(dut)


class AxiInterconnectMatrixCrossbar_3to3TC(AxiInterconnectMatrixCrossbar_1to1TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiInterconnectMatrixCrossbar(Axi4.R_CLS)
        dut.OUTPUTS = [{0, 1, 2}, {0, 1, 2}, {0, 1, 2}]
        dut.INPUT_CNT = 3
        cls.compileSim(dut)


AxiInterconnectMatrixCrossbar_TCs = [
    AxiInterconnectMatrixCrossbar_1to1TC,
    AxiInterconnectMatrixCrossbar_1to3TC,
    AxiInterconnectMatrixCrossbar_3to1TC,
    AxiInterconnectMatrixCrossbar_3to3TC,
]

if __name__ == "__main__":
    import unittest

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiInterconnectMatrixCrossbar_3to3TC("")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in AxiInterconnectMatrixCrossbar_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
