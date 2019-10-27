#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.constants import RESP_OKAY, PROT_DEFAULT
from hwtLib.ipif.axiLite2ipif import AxiLite2Ipif
from pyMathBitPrecise.bit_utils import mask
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer


class AxiLite2ipifTC(SimTestCase):
    CLK = CLK_PERIOD

    def setUp(self):
        pass

    def mySetUp(self, read_latency=0, write_latency=0):
        u = self.u = AxiLite2Ipif()
        DW = 32
        u.DATA_WIDTH = DW
        u.ADDR_WIDTH = 32
        self.m = mask(DW // 8)
        self.compileSimAndStart(u)
        ipif = u.m._ag
        ipif.READ_LATENCY = read_latency
        ipif.WRITE_LATENCY = write_latency
        SimTestCase.setUp(self)

    def test_nop(self):
        self.mySetUp()
        self.runSim(10 * self.CLK)

    def test_read(self, randomize_axi=False, read_latency=0):
        self.mySetUp(read_latency=read_latency)
        axi = self.u.s
        if randomize_axi:
            self.randomize(axi)

        ipif = self.u.m._ag
        MAGIC = 10
        ipif.mem[0] = MAGIC + 0
        ipif.mem[1] = MAGIC + 1
        ipif.mem[2] = MAGIC + 2
        ipif.mem[4] = MAGIC + 3

        axi.ar._ag.data.extend([
            (0, PROT_DEFAULT),
            (4, PROT_DEFAULT), 
            (8, PROT_DEFAULT),
            (16, PROT_DEFAULT)
        ])

        self.runSim(10 * (read_latency + 1) * self.CLK)

        self.assertValSequenceEqual(
            axi.r._ag.data,
            [(MAGIC + i, RESP_OKAY) for i in range(4)]
        )

    def test_write(self, randomize_axi=False, write_latency=0, data_delay=0):
        self.mySetUp(write_latency=write_latency)
        axi = self.u.s
        ipif = self.u.m
        if randomize_axi:
            self.randomize(axi)

        MAGIC = 10
        N = 4
        axi.aw._ag.data.extend([
            (i * 4, 0) for i in range(N)
        ])

        if data_delay > 0:

            def late_add_data():
                yield Timer(data_delay)
                axi.w._ag.data.extend([
                    (MAGIC + i, self.m) for i in range(N)
                ])

            self.procs.append(late_add_data())
        else:
            axi.w._ag.data.extend([
                (MAGIC + i, self.m) for i in range(N)
            ])
        self.runSim(20 * (write_latency + 1) * self.CLK)
        d = {k: int(v) for k, v in ipif._ag.mem.items()}
        self.assertDictEqual(d, {
            i: MAGIC + i for i in range(N)
        })

    def test_readAndWrite(self, randomize_axi=False,
                          read_latency=0, write_latency=0,
                          data_delay=0):
        self.mySetUp(read_latency=read_latency,
                     write_latency=write_latency)
        axi = self.u.s
        if randomize_axi:
            self.randomize(axi)

        ipif = self.u.m._ag
        MAGIC_R = 10
        MAGIC_W = 100

        N = 4

        for i in range(N):
            ipif.mem[i] = MAGIC_R + i
            axi.ar._ag.data.append((i * 4, PROT_DEFAULT))
            axi.aw._ag.data.append(((i + 4) * 4, PROT_DEFAULT))

        if data_delay > 0:
            def late_add_data(sim):
                yield Timer(data_delay)
                axi.w._ag.data.extend([
                    (MAGIC_W + i, self.m) for i in range(N)
                ])

            self.procs.append(late_add_data())
        else:
            axi.w._ag.data.extend([
                (MAGIC_W + i, self.m) for i in range(N)
            ])

        self.runSim(25 * (max(read_latency, write_latency) + 1) * self.CLK)

        self.assertValSequenceEqual(
            axi.r._ag.data,
            [(MAGIC_R + i, RESP_OKAY) for i in range(4)]
        )

        d = {k: int(v) for k, v in ipif.mem.items()}
        d_ref = {i: MAGIC_R + i for i in range(N)}
        d_ref.update({i + 4: MAGIC_W + i for i in range(N)})

        self.assertDictEqual(d, d_ref)

    def test_read_lat1(self, randomize_axi=False):
        self.test_read(randomize_axi, read_latency=1)

    def test_read_lat2(self, randomize_axi=False):
        self.test_read(randomize_axi, read_latency=1)

    def test_r_read_lat1(self):
        self.test_read_lat1(randomize_axi=True)

    def test_r_read_lat2(self):
        self.test_read_lat2(randomize_axi=True)

    def test_write_lat1(self, randomize_axi=False):
        self.test_write(randomize_axi, write_latency=1)

    def test_write_lat2(self, randomize_axi=False):
        self.test_write(randomize_axi, write_latency=1)

    def test_r_write_lat1(self):
        self.test_write_lat1(randomize_axi=True)

    def test_r_write_lat2(self):
        self.test_write_lat2(randomize_axi=True)

    def test_read_readAndWrite_lat1(self, randomize_axi=False):
        self.test_readAndWrite(randomize_axi, read_latency=1, write_latency=1)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AxiLite2ipifTC('test_read_lat1'))
    suite.addTest(unittest.makeSuite(AxiLite2ipifTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
