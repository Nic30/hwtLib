from _io import StringIO
import re
import unittest

from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.simulator.utils import pprintInterface, pprintAgents
from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hwtLib.amba.axi3Lite import Axi3Lite
from hwt.synthesizer.hObjList import HObjList


axi_str = """\
'axi'
    'axi_0'
        'axi_0.aw'
            'axi_0.aw.addr'
            'axi_0.aw.ready'
            'axi_0.aw.valid'
        'axi_0.ar'
            'axi_0.ar.addr'
            'axi_0.ar.ready'
            'axi_0.ar.valid'
        'axi_0.w'
            'axi_0.w.data'
            'axi_0.w.strb'
            'axi_0.w.ready'
            'axi_0.w.valid'
        'axi_0.r'
            'axi_0.r.data'
            'axi_0.r.resp'
            'axi_0.r.ready'
            'axi_0.r.valid'
        'axi_0.b'
            'axi_0.b.resp'
            'axi_0.b.ready'
            'axi_0.b.valid'
    'axi_1'
        'axi_1.aw'
            'axi_1.aw.addr'
            'axi_1.aw.ready'
            'axi_1.aw.valid'
        'axi_1.ar'
            'axi_1.ar.addr'
            'axi_1.ar.ready'
            'axi_1.ar.valid'
        'axi_1.w'
            'axi_1.w.data'
            'axi_1.w.strb'
            'axi_1.w.ready'
            'axi_1.w.valid'
        'axi_1.r'
            'axi_1.r.data'
            'axi_1.r.resp'
            'axi_1.r.ready'
            'axi_1.r.valid'
        'axi_1.b'
            'axi_1.b.resp'
            'axi_1.b.ready'
            'axi_1.b.valid'
    'axi_2'
        'axi_2.aw'
            'axi_2.aw.addr'
            'axi_2.aw.ready'
            'axi_2.aw.valid'
        'axi_2.ar'
            'axi_2.ar.addr'
            'axi_2.ar.ready'
            'axi_2.ar.valid'
        'axi_2.w'
            'axi_2.w.data'
            'axi_2.w.strb'
            'axi_2.w.ready'
            'axi_2.w.valid'
        'axi_2.r'
            'axi_2.r.data'
            'axi_2.r.resp'
            'axi_2.r.ready'
            'axi_2.r.valid'
        'axi_2.b'
            'axi_2.b.resp'
            'axi_2.b.ready'
            'axi_2.b.valid'
"""



clk_ag_str = """clk:<hwt.interfaces.agents.clk.ClockAgent object at 0x7f51335e5f60>
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

u_ag_str = """<hwt.interfaces.agents.clk.ClockAgent object at 0x7f2c812d4ef0>
    <hwt.interfaces.agents.rst.PullUpAgent object at 0x7f2c812d4f28>
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


class ExampleWithArrayAxi3Lite(EmptyUnit):
    def _declr(self):
        addClkRstn(self)
        self.axi = HObjList(Axi3Lite() for _ in range(3))


class SimulatorUtilsTC(SingleUnitSimTestCase):
    @classmethod
    def getUnit(cls):
        cls.u = ExampleWithArrayAxi3Lite()
        return cls.u

    def test_pprintInterface(self):
        u = self.u
        o = StringIO()
        pprintInterface(u.clk, file=o)
        self.assertEqual(o.getvalue(), "'clk'\n")

        o = StringIO()
        pprintInterface(u.axi, file=o)
        self.assertEqual(o.getvalue(), axi_str)

    def _test_pprintAgent(self, intf, expectedStr):
        pointerRe = re.compile("0x[a-f0-9]*")
        o = StringIO()
        pprintAgents(intf, file=o)
        self.assertEqual(pointerRe.sub(o.getvalue(), ""),
                         pointerRe.sub(expectedStr, ""))

    def test_pprintAgents(self):
        u = self.u
        self.runSim(1)

        self._test_pprintAgent(u.clk, clk_ag_str)
        self._test_pprintAgent(u.axi, axi_ag_str)
        self._test_pprintAgent(u, u_ag_str)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IpCorePackagerTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(SimulatorUtilsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
