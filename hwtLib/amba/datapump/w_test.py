#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axi3Lite import Axi3Lite
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtLib.amba.axis import axis_recieve_bytes
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.amba.datapump.r_aligned_test import Axi4_rDatapumpTC, Axi_datapumpTC
from hwtLib.amba.datapump.w import Axi_wDatapump
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class Axi4_wDatapumpTC(Axi_datapumpTC):
    LEN_MAX_VAL = Axi4_rDatapumpTC.LEN_MAX_VAL

    @classmethod
    def setUpClass(cls):
        cls.u = u = Axi_wDatapump(axiCls=Axi4)
        u.MAX_LEN = cls.LEN_MAX_VAL
        u.ALIGNAS = 8
        cls.compileSim(u)

    def wTrans(self, data, last, strb=mask(64 // 8), _id=0):
        return (data, strb, last)

    def bTrans(self, resp, _id=0):
        return (_id, resp)

    def spotMemcpyTransactions(self, base, len_: int, singleFrameLen: Optional[int]):
        """
        :param base: base address where to start
        :param len_: total number of words to copy - 1
        :param singleFrameLen: total max number of words in a single frame - 1
        """
        u = self.u
        addr_step = u.DATA_WIDTH // 8
        req = u.driver._ag.req
        wIn = u.driver.w._ag
        b = u.axi.b._ag.data
        assert base % addr_step == 0, base
        MAGIC = 100
        AXI_LEN_MAX = 2 ** u.axi.LEN_WIDTH
        if singleFrameLen is not None:
            AXI_LEN_MAX = min(AXI_LEN_MAX, singleFrameLen + 1)
        AXI_LEN_MAX = min(AXI_LEN_MAX, len_ + 1)

        for i in range(0, len_ + 1, self.LEN_MAX_VAL + 1):
            req.data.append(self.mkReq(base, len_))

        aw_ref = []
        for i in range(0, len_ + 1, AXI_LEN_MAX):
            len__ = min(AXI_LEN_MAX - 1, len_ - AXI_LEN_MAX * i)
            addr = base + i * addr_step
            a = self.aTrans(
                addr,
                len__,
                0
            )
            aw_ref.append(a)

        w_ref = []
        for i in range(len_ + 1):
            lastForDriver = (i + 1) % (self.LEN_MAX_VAL + 1) == 0 or i == len_
            lastForAxi = (i + 1) % AXI_LEN_MAX == 0
            last = lastForDriver or lastForAxi
            wIn.data.append((MAGIC + i, mask(addr_step), lastForDriver))
            w_ref.append(self.wTrans(MAGIC + i, last, mask(addr_step)))
            if last:
                b.append(self.bTrans(RESP_OKAY, 0))

        return aw_ref, w_ref

    def test_nop(self):
        u = self.u

        self.runSim(20 * CLK_PERIOD)

        self.assertEmpty(u.axi.aw._ag.data)
        self.assertEmpty(u.axi.w._ag.data)

    def test_simple(self):
        u = self.u

        req = u.driver._ag.req
        aw = u.axi.aw._ag.data

        # download one word from addr 0x100
        req.data.append(self.mkReq(0x100, 0))

        self.runSim(20 * CLK_PERIOD)

        self.assertValSequenceEqual(aw,
                                    [
                                        self.aTrans(0x100, 0, 0)
                                    ])

        self.assertEmpty(u.axi.w._ag.data)

    def test_simpleWithData(self):
        u = self.u

        req = u.driver._ag.req
        aw = u.axi.aw._ag.data
        wIn = u.driver.w._ag
        w = u.axi.w._ag.data
        b = u.axi.b._ag.data
        addr_step = u.DATA_WIDTH // 8

        # download one word from addr 0x100
        req.data.append(self.mkReq(0x100, 0))
        wIn.data.append((77, mask(addr_step), 1))
        b.append(self.bTrans(RESP_OKAY, _id=0))

        self.runSim(20 * CLK_PERIOD)

        self.assertValSequenceEqual(aw, [
            self.aTrans(0x100, 0, 0)
        ])

        self.assertValSequenceEqual(
            w, [self.wTrans(77, 1, strb=mask(addr_step), _id=0)])
        self.assertEmpty(b)

    def test_simpleUnaligned(self):
        u = self.u

        req = u.driver._ag.req
        aw = u.axi.aw._ag.data

        req.data.append(self.mkReq(0x101, 0))

        self.runSim(20 * CLK_PERIOD)
        if u.ALIGNAS == u.DATA_WIDTH:
            # unsupported alignment check if error is set
            self.assertEmpty(aw)
            self.assertValEqual(u.errorAlignment._ag.data[-1], 1)

        elif u.axi.LEN_WIDTH == 0:
            addr_step = u.DATA_WIDTH // 8
            # transaction has to be split
            self.assertValSequenceEqual(aw, [
                self.aTrans(0x100, 0, 0),
                self.aTrans(0x100 + addr_step, 0, 0),
            ])

            self.assertEmpty(u.axi.w._ag.data)
        else:
            # transaction has to be of len + 1
            self.assertValSequenceEqual(aw, [
                self.aTrans(0x100, 1, 0)
            ])

            self.assertEmpty(u.axi.w._ag.data)

    def test_simpleUnalignedWithData(self, N=1, WORDS=1, randomize=False):
        u = self.u

        req = u.driver._ag.req
        aw = u.axi.aw._ag.data
        wIn = u.driver.w._ag
        w = u.axi.w._ag.data
        b = u.axi.b._ag.data
        if randomize:
            self.randomize(u.driver.req)
            self.randomize(u.driver.w)
            self.randomize(u.axi.aw)
            self.randomize(u.axi.w)
            self.randomize(u.axi.b)

        addr_step = u.DATA_WIDTH // 8

        ref_w_frames = []
        for i in range(N):
            req.data.append(self.mkReq(0x101 + i * addr_step, WORDS - 1))
            frame = []
            for i2 in range(WORDS):
                isLast = (i2 == WORDS - 1)
                n0 = 0x10 * i2 + 0x20 + i
                n1 = 0x10 * i2 + 0x10 + i
                # aligned input data word
                wIn.data.append(((n1 << ((addr_step - 1) * 8)) | n0, mask(addr_step), isLast))
                frame.extend([n0, 0, 0, 0, 0, 0, 0, n1, ])
            ref_w_frames.append(frame)
            b.append(self.bTrans(RESP_OKAY, 0))

        t = (15 + N) * CLK_PERIOD
        if randomize:
            t *= 6
        self.runSim(t)
        if u.ALIGNAS == u.DATA_WIDTH:
            # unsupported alignment check if error is set
            self.assertEmpty(aw)
            self.assertValEqual(u.errorAlignment._ag.data[-1], 1)

        else:
            aw_ref = []
            if u.axi.LEN_WIDTH == 0:
                for i in range(N):
                    for w_i in range(WORDS + 1):
                        aw_ref.append(
                            self.aTrans(0x100 + (i + w_i) * addr_step, WORDS, 0)
                        )
            else:
                for i in range(N):
                    aw_ref.append(
                        self.aTrans(0x100 + i * addr_step, WORDS, 0)
                    )
            self.assertValSequenceEqual(aw, aw_ref)

            for ref_frame in ref_w_frames:
                if hasattr(u.axi.w, "id"):
                    offset, id_, w_data = axis_recieve_bytes(u.axi.w)
                    self.assertEqual(id_, 0)
                elif u.axi.LEN_WIDTH == 0:
                    offset = None
                    w_data = []
                    for w_i in range(WORDS + 1):
                        data, strb = w.popleft()
                        for B_i in range(addr_step):
                            if strb[B_i]:
                                if offset is None:
                                    offset = B_i + (addr_step * w_i)
                                B = int(data[(B_i + 1) * 8: B_i * 8])
                                w_data.append(B)
                else:
                    offset, w_data = axis_recieve_bytes(u.axi.w)
                self.assertEqual(offset, 1)
                self.assertSequenceEqual(w_data, ref_frame)

            self.assertEmpty(w)
            self.assertEmpty(b)

    def test_simpleUnalignedWithData_5x(self):
        self.test_simpleUnalignedWithData(N=5)

    def test_simpleUnalignedWithData_5x_r(self):
        self.test_simpleUnalignedWithData(N=5, randomize=True)

    def test_simpleUnalignedWithData_5x_2words_r(self):
        self.test_simpleUnalignedWithData(N=5, WORDS=2, randomize=True)

    def test_simpleUnalignedWithData_5x_3words_r(self):
        self.test_simpleUnalignedWithData(N=5, WORDS=3, randomize=True)

    def test_singleLong(self):
        self.test_multiple_randomized(N=1, transLen=self.LEN_MAX_VAL, randomize=False)

    def test_multiple(self):
        self.test_multiple_randomized(N=50, transLen=0, randomize=False)

    def test_multiple_randomized(self, N=50, transLen=0, singleFrameLen=None, randomize=True):
        u = self.u
        aw = u.axi.aw._ag.data
        w = u.axi.w._ag.data
        b = u.axi.b._ag.data

        aw_ref, w_ref = [], []
        for i in range(N):
            _aw_ref, _w_ref = self.spotMemcpyTransactions((i * 8) + 0x100, transLen, singleFrameLen)
            aw_ref.extend(_aw_ref)
            w_ref.extend(_w_ref)

        if randomize:
            ra = self.randomize
            ra(u.axi.aw)
            ra(u.axi.b)
            ra(u.driver.req)
            ra(u.driver.ack)
            ra(u.axi.w)
            ra(u.driver.w)

        self.runSim(N * (transLen + 1) * 8 * CLK_PERIOD)

        self.assertValSequenceEqual(aw, aw_ref)
        self.assertValSequenceEqual(w, w_ref)
        self.assertEmpty(b)
        self.assertEqual(len(u.driver._ag.ack.data), N)

    def test_multiple_randomized2(self):
        self.test_multiple_randomized(transLen=3)


class Axi3_wDatapump_direct_TC(Axi4_wDatapumpTC):
    LEN_MAX_VAL = 15

    def wTrans(self, data, last, strb=mask(64 // 8), _id=0):
        return (_id, data, strb, last)

    @classmethod
    def setUpClass(cls):
        u = Axi_wDatapump(axiCls=Axi3)
        u.MAX_LEN = 16
        u.ALIGNAS = 8
        cls.compileSim(u)


class Axi3_wDatapump_small_splitting_TC(SimTestCase):
    LEN_MAX_VAL = 3
    CHUNK_WIDTH = 32
    DATA_WIDTH = 32

    def wTrans(self, data, last, strb=mask(64 // 8), _id=0):
        return Axi3_wDatapump_direct_TC.wTrans(self, data, last, strb, _id)

    def bTrans(self, resp, _id=0):
        return Axi3_wDatapump_direct_TC.bTrans(self, resp, _id)

    def mkReq(self, addr, _len, rem=0, _id=0):
        return Axi3_wDatapump_direct_TC.mkReq(self, addr, _len, rem, _id)

    @classmethod
    def setUpClass(cls):
        u = cls.u = Axi_wDatapump(axiCls=Axi3)
        u.DATA_WIDTH = u.ALIGNAS = u.CHUNK_WIDTH = cls.DATA_WIDTH
        u.MAX_CHUNKS = (cls.DATA_WIDTH // cls.CHUNK_WIDTH) * (cls.LEN_MAX_VAL + 1)

        cls.compileSim(u)

    def test_1024random(self):
        u = self.u
        req = u.driver._ag.req
        wIn = u.driver.w._ag
        dataMask = mask(u.DATA_WIDTH // 8)

        m = AxiSimRam(axi=u.axi)
        N = 1024
        data = [self._rand.getrandbits(u.DATA_WIDTH) for _ in range(N)]

        buff = m.malloc(N * (u.DATA_WIDTH // 8))

        dataIt = iter(data)
        end = False
        addr = 0
        while True:
            frameSize = self._rand.getrandbits(self.LEN_MAX_VAL.bit_length()) + 1
            frame = []
            try:
                for _ in range(frameSize):
                    frame.append(next(dataIt))
            except StopIteration:
                end = True

            if frame:
                req.data.append(self.mkReq(addr, len(frame) - 1))
                wIn.data.extend([(d, dataMask, i == len(frame) - 1)
                                 for i, d in enumerate(frame)])
                addr += len(frame) * u.DATA_WIDTH // 8
            if end:
                break

        ra = self.randomize
        ra(u.axi.aw)
        ra(u.axi.b)
        ra(u.driver.req)
        ra(u.driver.ack)
        ra(u.axi.w)
        ra(u.driver.w)

        self.runSim(N * 5 * CLK_PERIOD)

        inMem = m.getArray(buff, u.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(inMem, data)


class Axi3_wDatapump_small_splitting_alignas8_TC(Axi3_wDatapump_small_splitting_TC):
    LEN_MAX_VAL = 3
    CHUNK_WIDTH = 8
    DATA_WIDTH = 32

    @classmethod
    def setUpClass(cls):
        u = cls.u = Axi_wDatapump(axiCls=Axi3)
        u.DATA_WIDTH = cls.DATA_WIDTH
        u.ALIGNAS = 8
        u.CHUNK_WIDTH = cls.CHUNK_WIDTH
        u.MAX_CHUNKS = (cls.DATA_WIDTH // cls.CHUNK_WIDTH) * (cls.LEN_MAX_VAL + 1)

        cls.compileSim(u)


class Axi4_wDatapump_alignas8TC(Axi4_wDatapumpTC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = Axi_wDatapump(axiCls=Axi4)
        u.MAX_LEN = cls.LEN_MAX_VAL
        u.ALIGNAS = 8
        cls.compileSim(u)


class Axi3Lite_wDatapumpTC(Axi4_wDatapumpTC):
    LEN_MAX_VAL = 3

    @classmethod
    def setUpClass(cls):
        cls.u = u = Axi_wDatapump(axiCls=Axi3Lite)
        u.MAX_LEN = cls.LEN_MAX_VAL
        cls.compileSim(u)

    def mkReq(self, addr, _len, rem=0, _id=0):
        return (addr, _len, rem)

    def wTrans(self, data, last, strb=mask(64 // 8), _id=0):
        return (data, strb)

    def bTrans(self, resp, _id=0):
        return resp


class Axi4Lite_wDatapumpTC(Axi3Lite_wDatapumpTC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = Axi_wDatapump(axiCls=Axi4Lite)
        u.MAX_LEN = cls.LEN_MAX_VAL
        cls.compileSim(u)


class Axi4Lite_wDatapump_alignas8TC(Axi4Lite_wDatapumpTC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = Axi_wDatapump(axiCls=Axi4Lite)
        u.MAX_LEN = cls.LEN_MAX_VAL
        u.ALIGNAS = 8
        cls.compileSim(u)


Axi_wDatapumpTCs = [
    Axi4_wDatapumpTC,
    Axi3_wDatapump_direct_TC,
    Axi3_wDatapump_small_splitting_TC,
    Axi3_wDatapump_small_splitting_alignas8_TC,
    Axi4_wDatapump_alignas8TC,
    Axi3Lite_wDatapumpTC,
    Axi4Lite_wDatapumpTC,
    Axi4Lite_wDatapump_alignas8TC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4Lite_wDatapump_alignas8TC('test_simpleUnalignedWithData'))
    for tc in Axi_wDatapumpTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
