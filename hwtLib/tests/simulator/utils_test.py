#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import StringIO
import re

from hwt.hwIO import HwIO
from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.utils import addClkRstn
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import pprintHwIO, pprintAgents
from hwtLib.abstract.emptyHwModule import EmptyHwModule
from hwtLib.amba.axi3Lite import Axi3Lite


axi_str = """\
'axi'
    'axi.0'
        'axi.0.ar'
            'axi.0.ar.addr'
            'axi.0.ar.ready'
            'axi.0.ar.valid'
        'axi.0.r'
            'axi.0.r.data'
            'axi.0.r.resp'
            'axi.0.r.ready'
            'axi.0.r.valid'
        'axi.0.aw'
            'axi.0.aw.addr'
            'axi.0.aw.ready'
            'axi.0.aw.valid'
        'axi.0.w'
            'axi.0.w.data'
            'axi.0.w.strb'
            'axi.0.w.ready'
            'axi.0.w.valid'
        'axi.0.b'
            'axi.0.b.resp'
            'axi.0.b.ready'
            'axi.0.b.valid'
    'axi.1'
        'axi.1.ar'
            'axi.1.ar.addr'
            'axi.1.ar.ready'
            'axi.1.ar.valid'
        'axi.1.r'
            'axi.1.r.data'
            'axi.1.r.resp'
            'axi.1.r.ready'
            'axi.1.r.valid'
        'axi.1.aw'
            'axi.1.aw.addr'
            'axi.1.aw.ready'
            'axi.1.aw.valid'
        'axi.1.w'
            'axi.1.w.data'
            'axi.1.w.strb'
            'axi.1.w.ready'
            'axi.1.w.valid'
        'axi.1.b'
            'axi.1.b.resp'
            'axi.1.b.ready'
            'axi.1.b.valid'
    'axi.2'
        'axi.2.ar'
            'axi.2.ar.addr'
            'axi.2.ar.ready'
            'axi.2.ar.valid'
        'axi.2.r'
            'axi.2.r.data'
            'axi.2.r.resp'
            'axi.2.r.ready'
            'axi.2.r.valid'
        'axi.2.aw'
            'axi.2.aw.addr'
            'axi.2.aw.ready'
            'axi.2.aw.valid'
        'axi.2.w'
            'axi.2.w.data'
            'axi.2.w.strb'
            'axi.2.w.ready'
            'axi.2.w.valid'
        'axi.2.b'
            'axi.2.b.resp'
            'axi.2.b.ready'
            'axi.2.b.valid'
"""

clk_ag_str = """clk:<hwt.hwIOs.agents.clk.ClockAgent object at 0x7f51335e5f60>
"""
axi_ag_str = """axi:
    p0:<hwtLib.amba.axiLite.AxiLiteAgent object at 0x7f5133600208>
        <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f5133600160>
        <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f5133600198>
        <hwtLib.amba.axiLite.AxiLite_wAgent object at 0x7f5133600470>
        <hwtLib.amba.axiLite.AxiLite_rAgent object at 0x7f51336003c8>
        <hwtLib.amba.axiLite.AxiLite_bAgent object at 0x7f5133600518>
    p1:<hwtLib.amba.axiLite.AxiLiteAgent object at 0x7f51336005c0>
        <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f51336006a0>
        <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f51336005f8>
        <hwtLib.amba.axiLite.AxiLite_wAgent object at 0x7f51336007f0>
        <hwtLib.amba.axiLite.AxiLite_rAgent object at 0x7f5133600748>
        <hwtLib.amba.axiLite.AxiLite_bAgent object at 0x7f5133600898>
    p2:<hwtLib.amba.axiLite.AxiLiteAgent object at 0x7f5133600940>
        <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f5133600a20>
        <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f5133600978>
        <hwtLib.amba.axiLite.AxiLite_wAgent object at 0x7f5133600b70>
        <hwtLib.amba.axiLite.AxiLite_rAgent object at 0x7f5133600ac8>
        <hwtLib.amba.axiLite.AxiLite_bAgent object at 0x7f5133600c18>
"""

u_ag_str = """<hwt.hwIOs.agents.clk.ClockAgent object at 0x7f2c812d4ef0>
    <hwt.hwIOs.agents.rst.PullUpAgent object at 0x7f2c812d4f28>
    axi:
        p0:<hwtLib.amba.axiLite.AxiLiteAgent object at 0x7f2c812f0198>
            <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f2c812f00f0>
            <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f2c812f0128>
            <hwtLib.amba.axiLite.AxiLite_wAgent object at 0x7f2c812f0400>
            <hwtLib.amba.axiLite.AxiLite_rAgent object at 0x7f2c812f0358>
            <hwtLib.amba.axiLite.AxiLite_bAgent object at 0x7f2c812f04a8>
        p1:<hwtLib.amba.axiLite.AxiLiteAgent object at 0x7f2c812f0550>
            <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f2c812f0630>
            <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f2c812f0588>
            <hwtLib.amba.axiLite.AxiLite_wAgent object at 0x7f2c812f0780>
            <hwtLib.amba.axiLite.AxiLite_rAgent object at 0x7f2c812f06d8>
            <hwtLib.amba.axiLite.AxiLite_bAgent object at 0x7f2c812f0828>
        p2:<hwtLib.amba.axiLite.AxiLiteAgent object at 0x7f2c812f08d0>
            <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f2c812f09b0>
            <hwtLib.amba.axiLite.AxiLite_addrAgent object at 0x7f2c812f0908>
            <hwtLib.amba.axiLite.AxiLite_wAgent object at 0x7f2c812f0b00>
            <hwtLib.amba.axiLite.AxiLite_rAgent object at 0x7f2c812f0a58>
            <hwtLib.amba.axiLite.AxiLite_bAgent object at 0x7f2c812f0ba8>
"""


class ExampleWithArrayAxi3Lite(EmptyHwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.axi = HwIOArray(Axi3Lite() for _ in range(3))


class SimulatorUtilsTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = ExampleWithArrayAxi3Lite()
        cls.compileSim(cls.dut)

    def test_pprintInterface(self):
        dut = self.dut
        o = StringIO()
        pprintHwIO(dut.clk, file=o)
        self.assertEqual(o.getvalue(), "'clk'\n")

        o = StringIO()
        pprintHwIO(dut.axi, file=o)
        self.assertEqual(o.getvalue(), axi_str)

    def _test_pprintAgent(self, hwIO: HwIO, expectedStr: str):
        pointerRe = re.compile("0x[a-f0-9]*")
        o = StringIO()
        pprintAgents(hwIO, file=o)
        self.assertEqual(pointerRe.sub(o.getvalue(), ""),
                         pointerRe.sub(expectedStr, ""))

    def test_pprintAgents(self):
        dut = self.dut
        self.runSim(1)

        self._test_pprintAgent(dut.clk, clk_ag_str)
        self._test_pprintAgent(dut.axi, axi_ag_str)
        self._test_pprintAgent(dut, u_ag_str)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SimulatorUtilsTC("test_sWithStartPadding")])
    suite = testLoader.loadTestsFromTestCase(SimulatorUtilsTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
