#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axiLite_comp.endpoint_test import addrGetter
from hwtLib.amba.axi_comp.tester import AxiTester, SEND_AR, RECV_R
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster
from hwtLib.amba.constants import BYTES_IN_TRANS, PROT_DEFAULT, LOCK_DEFAULT,\
    CACHE_DEFAULT, BURST_INCR, RESP_OKAY
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.bitmask import mask
from itertools import islice
from collections import deque


class SimProcessSequence(deque):
    def onPartDone(self, sim):
        if self:
            self.actual = actual = self.popleft()
            actual(sim, self.onPartDone)
        else:
            self.actual = None

    def run(self, sim):
        self.actual = actual = self.popleft()
        actual(sim, self.onPartDone)
        return
        yield


class AxiTesterTC(SimTestCase):
    def setUp(self):
        super(AxiTesterTC, self).setUp()

        self.u = u = AxiTester(Axi3)
        u.DATA_WIDTH.set(32)

        self.prepareUnit(u, onAfterToRtl=self.mkRegisterMap)
        self.m = Axi3DenseMem(u.clk, u.m_axi)

    def mkRegisterMap(self, u, modelCls):
        bus = u.cntrl
        self.addrProbe = AddressSpaceProbe(bus, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(bus, self.addrProbe.discovered)

    def randomize_all(self):
        axi = self.u.m_axi

        self.randomize(axi.aw)
        self.randomize(axi.ar)
        self.randomize(axi.w)
        self.randomize(axi.r)
        self.randomize(axi.b)

    def test_nop(self):
        self.randomize_all()
        self.runSim(200 * Time.ns)

    def poolWhileBussy(self, sim, onReady):
        def repeatWaitIfNotReady(sim):
            d = self.u.cntrl.r._ag.data[-1][0]
            d = int(d)
            if d:
                # ready, run callback
                onReady(sim)
            else:
                # not ready pool again
                self.poolWhileBussy(sim, onReady)

        self.regs.cmd_and_status.read(onDone=repeatWaitIfNotReady)

    def test_read(self):
        self.randomize_all()
        r = self.regs
        m = self.m
        WORD_SIZE = int(self.u.DATA_WIDTH) // 8
        ID_WIDTH = int(self.u.ID_WIDTH)
        ID_MASK = mask(ID_WIDTH)
        cntrl_r = self.u.cntrl.r._ag.data

        MAGIC = 89
        expected_data = []
        self.transactionCompleted = 0

        transactions = [(1, 1), (2, 3), (3, 8)]
        tIt = iter(transactions)

        def spotNewTransaction(sim, onDone):
            try:
                id_, words = next(tIt)
            except StopIteration:
                return

            magic = MAGIC * id_
            initValues = [magic + i for i in range(words)]
            memPtr = m.calloc(words, WORD_SIZE,
                              initValues=initValues)
            expected_data.append(initValues)
            self.expected_id = id_

            r.ar_aw_w_id.write(id_)
            r.addr.write(memPtr)
            r.burst.write(BURST_INCR)
            r.cache.write(CACHE_DEFAULT)
            r.len.write(words - 1)
            r.lock.write(LOCK_DEFAULT)
            r.prot.write(PROT_DEFAULT)
            r.size.write(BYTES_IN_TRANS(WORD_SIZE))
            r.qos.write(0)

            self.wordIt = iter_with_last(initValues)
            r.cmd_and_status.write(SEND_AR, onDone=onDone)

        def data_read_req(sim, onDone):
            try:
                self.extected_last, self.extected_d = next(self.wordIt)
            except StopIteration:
                raise Exception("Underflow")
            r.cmd_and_status.write(RECV_R, onDone=onDone)

        def data_read_regisers(sim, onDone):
            # 3
            r.r_id.read()
            r.r_data.read()
            r.r_resp.read()
            r.r_last.read(onDone=onDone)

        def checkBeat(sim, onDone):
            trans_id = cntrl_r[-4][0]
            trans_data = cntrl_r[-3][0]
            trans_resp = cntrl_r[-2][0]
            trans_last = cntrl_r[-1][0]

            for t in islice(cntrl_r, len(cntrl_r) - 4, len(cntrl_r)):
                self.assertValEqual(t[1], RESP_OKAY)

            id_, d, last = self.expected_id, self.extected_d, self.extected_last
            self.assertValEqual(trans_id & ID_MASK, id_)
            self.assertValEqual(trans_data, d)
            self.assertValEqual(trans_resp & 0b11, RESP_OKAY)
            self.assertValEqual(trans_last & 1, last)
            self.transactionCompleted += 1
            onDone(sim)

        pool = self.poolWhileBussy
        seq = SimProcessSequence()
        for _, len_ in transactions:
            seq.extend([
                pool,
                spotNewTransaction
            ])
            for _ in range(len_):
                seq.extend([
                    pool,
                    data_read_req,
                    pool,
                    data_read_regisers,
                    checkBeat,
                ])
        self.procs.append(seq.run)
        self.runSim(4000 * Time.ns)
        self.assertEmpty(seq)
        self.assertEqual(len(self.u.cntrl.w._ag.data), 0)
        self.assertEqual(self.transactionCompleted, sum([x[1] for x in transactions]))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_wDatapumpTC('test_singleLong'))
    suite.addTest(unittest.makeSuite(AxiTesterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
