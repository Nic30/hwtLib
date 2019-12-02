from collections import deque
from itertools import chain

from hwt.code import log2ceil
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.constants import PROT_DEFAULT, BYTES_IN_TRANS,\
    QOS_DEFAULT, CACHE_DEFAULT, LOCK_DEFAULT, BURST_INCR
from hwtLib.amba.interconnect.matrixAddrCrossbar import AxiInterconnectMatrixAddrCrossbar
from pycocotb.agents.clk import DEFAULT_CLOCK


class AxiInterconnectMatrixAddrCrossbar_1to1TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        u.MASTERS = [{0}]
        u.SLAVES = [
            (0x0000, 0x1000),
        ]
        u.ADDR_WIDTH = log2ceil(0x1000 - 1)
        return u

    def addr_transaction(self, id_, addr, len_):
        axi = self.u.master[0]

        burst = BURST_INCR
        cache = CACHE_DEFAULT
        lock = LOCK_DEFAULT
        prot = PROT_DEFAULT
        size = BYTES_IN_TRANS(axi.DATA_WIDTH // 8)
        qos = QOS_DEFAULT

        return (
            id_,
            addr,
            burst,
            cache,
            len_,
            lock,
            prot,
            size,
            qos,
        )

    def randomize_all(self):
        u = self.u
        for i in u.slave:
            self.randomize(i)

        for i in u.master:
            self.randomize(i)

        if u.REQUIRED_ORDER_SYNC_M_FOR_S:
            for i in u.order_m_index_for_s_data_out:
                self.randomize(i)
        if u.REQUIRED_ORDER_SYNC_S_FOR_M:
            for i in u.order_s_index_for_m_data_out:
                self.randomize(i)

    def test_nop(self):
        u = self.u
        self.randomize_all()

        self.runSim(10 * DEFAULT_CLOCK)
        for i in chain(u.master, u.slave):
            self.assertEmpty(i._ag.data)

        if u.REQUIRED_ORDER_SYNC_M_FOR_S:
            for i in u.order_m_index_for_s_data_out:
                self.assertEmpty(i._ag.data)
        if u.REQUIRED_ORDER_SYNC_S_FOR_M:
            for i in u.order_s_index_for_m_data_out:
                self.assertEmpty(i._ag.data)

    def test_all(self, transaction_cnt=10, magic=0):
        """
        :param transaction_cnt: transactions per master per connected slave 
        """
        u = self.u
        for m in u.master:
            # to automatically set addr.size
            m.DATA_WIDTH = 64
        self.randomize_all()

        slave_a_transactions = [
            [deque() for _ in u.master]
            for _ in u.slave
        ]
        for master_i, (accesible_slaves, m) in enumerate(zip(u.MASTERS, u.master)):
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

        max_trans_duration = max(len(m._ag.data) for m in u.master)
        self.runSim((40 + 4 * max_trans_duration *
                     transaction_cnt) * DEFAULT_CLOCK)
        # assert all data was send
        for m_i, m in enumerate(u.master):
            self.assertEmpty(m._ag.data, "master: %d" % m_i)

        if u.REQUIRED_ORDER_SYNC_S_FOR_M:
            # assert order_s_index_for_m_data_out contains the slave indexes as expected by address
            for m_i, s_for_m in enumerate(u.order_s_index_for_m_data_out):
                ref_s_for_m = []
                for slave_i, slave_a in enumerate(slave_a_transactions):
                    if slave_i not in accesible_slaves:
                        continue

                    slave_addr_offset = self.u.SLAVES[slave_i][0]
                    for _ in range(transaction_cnt):
                        ref_s_for_m.append(slave_i)
                self.assertValSequenceEqual(
                    s_for_m._ag.data, ref_s_for_m, "master: %d" % m_i)

        if u.REQUIRED_ORDER_SYNC_M_FOR_S:
            # use order from u.order_m_index_for_s_data_out to rebuild original
            # order of transactions
            for s_i, (s, m_for_s, s_all_ref) in enumerate(zip(
                    u.slave, u.order_m_index_for_s_data_out, slave_a_transactions)):
                s = s._ag.data
                m_for_s = [int(m) for m in m_for_s._ag.data]
                trans_cnt = sum([len(r) for r in s_all_ref])
                self.assertEqual(len(m_for_s), trans_cnt, "slave: %d" % s_i)
                self.assertEqual(len(s), trans_cnt, "slave: %d" % s_i)
                s_ref = []
                for m_i in m_for_s:
                    t = s_all_ref[m_i].popleft()
                    s_ref.append(t)

                self.assertValSequenceEqual(s, s_ref, "slave: %d" % s_i)
        else:
            # check the address transactions arrived correctly on slave
            for s_i, (s, s_all_ref) in enumerate(zip(
                    u.slave, slave_a_transactions)):
                s = s._ag.data
                assert len(s_all_ref) == 1
                s_ref = s_all_ref[0]
                self.assertValSequenceEqual(s, s_ref, "slave: %d" % s_i)


class AxiInterconnectMatrixAddrCrossbar_1to3TC(AxiInterconnectMatrixAddrCrossbar_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        u.MASTERS = [{0, 1, 2}]
        u.SLAVES = [
            (0x0000, 0x1000),
            (0x1000, 0x1000),
            (0x2000, 0x1000),
        ]
        u.ADDR_WIDTH = log2ceil(0x4000 - 1)
        return u


class AxiInterconnectMatrixAddrCrossbar_3to1TC(AxiInterconnectMatrixAddrCrossbar_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        u.MASTERS = [{0}, {0}, {0}]
        u.SLAVES = [
            (0x0000, 0x1000),
        ]
        u.ADDR_WIDTH = log2ceil(0x2000 - 1)
        return u


class AxiInterconnectMatrixAddrCrossbar_3to3TC(AxiInterconnectMatrixAddrCrossbar_1to1TC):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiInterconnectMatrixAddrCrossbar(Axi4.AR_CLS)
        #u.MASTERS = [{0, 1}, {0, 1}]
        #u.SLAVES = [
        #    (0x0000, 0x1000),
        #    (0x1000, 0x1000),
        #]

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
    # suite.addTest(AxiInterconnectMatrixAddrCrossbar_3to3TC(''))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixAddrCrossbar_1to1TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixAddrCrossbar_1to3TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixAddrCrossbar_3to1TC))
    suite.addTest(unittest.makeSuite(AxiInterconnectMatrixAddrCrossbar_3to3TC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
