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


class AxiTesterTC(SimTestCase):
    def setUp(self):
        super(AxiTesterTC, self).setUp()

        self.u = u = AxiTester(Axi3)
        u.DATA_WIDTH.set(32)

        self.prepareUnit(u, onAfterToRtl=self.mkRegisterMap)
        self.m = Axi3DenseMem(u.clk, u.axi)

    def mkRegisterMap(self, u, modelCls):
        bus = u.cntrl
        self.addrProbe = AddressSpaceProbe(bus, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(bus, self.addrProbe.discovered)

    def randomize_all(self):
        axi = self.u.axi

        self.randomize(axi.aw)
        self.randomize(axi.ar)
        self.randomize(axi.w)
        self.randomize(axi.r)
        self.randomize(axi.b)

    def test_nop(self):
        self.randomize_all()
        self.runSim(200 * Time.ns)

    def poolWhileBussy(self, onReady):
        def repeatWaitIfNotReady(sim):
            d = self.u.cntrl.r._ag.data[-1][0]
            d = int(d)
            print(sim.now, "pooling", d)
            if d:
                # ready, run callback
                onReady(sim)
            else:
                # not ready pool again
                pool_wait(sim)

        def pool_wait(sim):
            self.regs.cmd_and_status.read(onDone=repeatWaitIfNotReady)

        return pool_wait

    def test_read(self):
        self.randomize_all()
        r = self.regs
        m = self.m
        WORD_SIZE = int(self.u.DATA_WIDTH) // 8
        cntrl_r = self.u.cntrl.r._ag.data

        MAGIC = 89
        expected_data = []
        self.transactionCompleted = 0

        transactions = [(1, 1), (3, 2), (8, 3)]
        tIt = iter(transactions)

        def spotNewTransaction(sim):
            id_, words = next(tIt)
            schedule_transaction(id_, words, spotNewTransaction)

        def schedule_transaction(id_, words, onDone):
            magic = MAGIC * id_
            initValues = [magic + i for i in range(words)]
            memPtr = m.calloc(words, WORD_SIZE,
                              initValues=initValues)
            expected_data.append(initValues)

            # 1
            r.ar_aw_w_id.write(id_)
            r.addr.write(memPtr)
            r.burst.write(BURST_INCR)
            r.cache.write(CACHE_DEFAULT)
            r.len.write(words - 1)
            r.lock.write(LOCK_DEFAULT)
            r.prot.write(PROT_DEFAULT)
            r.size.write(BYTES_IN_TRANS(WORD_SIZE))
            r.qos.write(0)

            dataIter = iter_with_last(initValues)

            def data_read(sim, onDone=None):
                # 3
                last, d = next(dataIter)

                def checkId(sim):
                    self.assertValSequenceEqual(cntrl_r[-1], [id_, RESP_OKAY])
                r.r_id.read(onDone=checkId)

                def checkData(sim):
                    self.assertValSequenceEqual(cntrl_r[-1], [d, RESP_OKAY])
                r.r_data.read(onDone=checkData)

                def checkResp(sim):
                    self.assertValEqual(cntrl_r[-1], [RESP_OKAY, RESP_OKAY])
                r.r_resp.read(onDone=checkResp)

                def checkLast(sim):
                    #global transactionCompleted
                    print("framw ", self.transactionCompleted, " ok")
                    self.assertValEqual(cntrl_r[-1], [last, RESP_OKAY])
                    self.transactionCompleted += 1

                    if onDone:
                        # 4
                        onDone(sim)

                r.r_last.read(onDone=checkLast)

            def afterAW_send(sim):
                # 2
                for last, _ in iter_with_last(range(words)):
                    if last:
                        def callback(sim):
                            return data_read(sim, onDone)
                    else:
                        callback = data_read

                    r.cmd_and_status.write(RECV_R,
                                           onDone=self.poolWhileBussy(callback))
            r.cmd_and_status.write(SEND_AR, onDone=self.poolWhileBussy(afterAW_send))

        spotNewTransaction(None)
        self.runSim(2000 * Time.ns)
        self.assertEqual(len(self.u.cntrl.w._ag.data), 0)
        self.assertEqual(self.transactionCompleted, 3)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_wDatapumpTC('test_singleLong'))
    suite.addTest(unittest.makeSuite(AxiTesterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
