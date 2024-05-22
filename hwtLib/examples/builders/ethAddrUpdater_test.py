#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi_comp.sim.ram import Axi4SimRam
from hwtLib.examples.builders.ethAddrUpdater import EthAddrUpdater, \
    frameHeader
from hwtSimApi.constants import CLK_PERIOD


class EthAddrUpdater_dw64_alaignas64TC(SimTestCase):
    DW = 64
    AW = 32
    ALIGNAS = DW
    OFFSET = 0

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = EthAddrUpdater()
        dut.DATA_WIDTH = cls.DW
        dut.ADDR_WIDTH = cls.AW
        dut.ALIGNAS = cls.ALIGNAS
        cls.compileSim(dut)

    def test_simpleOp(self):
        DW = self.DW
        dut = self.dut
        r = self.randomize
        r(dut.axi_m.ar)
        r(dut.axi_m.r)
        r(dut.axi_m.aw)
        r(dut.axi_m.w)
        r(dut.axi_m.b)

        m = Axi4SimRam(dut.axi_m)
        tmpl = TransTmpl(frameHeader)
        frameTmpl = list(FrameTmpl.framesFromTransTmpl(tmpl, DW))[0]

        def randFrame():
            rand = self._rand.getrandbits
            data = {"eth": {"src": rand(48),
                            "dst": rand(48),
                            },
                    "ipv4": {"src": rand(32),
                             "dst": rand(32),
                            }
                    }
            d = list(frameTmpl.packData(data))
            ptr = m.calloc(ceil(frameHeader.bit_length() / DW),
                           DW // 8,
                           initValues=d,
                           keepOut=self.OFFSET,
                           )
            return ptr, data

        framePtr, frameData = randFrame()
        dut.packetAddr._ag.data.append(framePtr)

        self.runSim(100 * CLK_PERIOD)
        updatedFrame = m.getStruct(framePtr, tmpl)
        self.assertValEqual(updatedFrame.eth.src, frameData["eth"]['dst'])
        self.assertValEqual(updatedFrame.eth.dst, frameData["eth"]['src'])
        self.assertValEqual(updatedFrame.ipv4.src, frameData["ipv4"]['dst'])
        self.assertValEqual(updatedFrame.ipv4.dst, frameData["ipv4"]['src'])


class EthAddrUpdater_dw64_alaignas8TC(EthAddrUpdater_dw64_alaignas64TC):
    ALIGNAS = 8
    OFFSET = 1


EthAddrUpdaterTCs = [
    EthAddrUpdater_dw64_alaignas64TC,
    EthAddrUpdater_dw64_alaignas8TC
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([EthAddrUpdaterTC("test_simpleOp")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in EthAddrUpdaterTCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
