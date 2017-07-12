from _io import StringIO
import re
import unittest

from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import pprintInterface, pprintAgents
from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hwtLib.amba.axiLite import AxiLite


axi_str = """'axi'
    'axi.aw'
        'axi.aw.addr'
        'axi.aw.ready'
        'axi.aw.valid'
    'axi.ar'
        'axi.ar.addr'
        'axi.ar.ready'
        'axi.ar.valid'
    'axi.w'
        'axi.w.data'
        'axi.w.strb'
        'axi.w.ready'
        'axi.w.valid'
    'axi.r'
        'axi.r.data'
        'axi.r.resp'
        'axi.r.ready'
        'axi.r.valid'
    'axi.b'
        'axi.b.resp'
        'axi.b.ready'
        'axi.b.valid'
    p0:'axi'
        'axi.aw'
            'axi.aw.addr'
            'axi.aw.ready'
            'axi.aw.valid'
        'axi.ar'
            'axi.ar.addr'
            'axi.ar.ready'
            'axi.ar.valid'
        'axi.w'
            'axi.w.data'
            'axi.w.strb'
            'axi.w.ready'
            'axi.w.valid'
        'axi.r'
            'axi.r.data'
            'axi.r.resp'
            'axi.r.ready'
            'axi.r.valid'
        'axi.b'
            'axi.b.resp'
            'axi.b.ready'
            'axi.b.valid'
    p1:'axi'
        'axi.aw'
            'axi.aw.addr'
            'axi.aw.ready'
            'axi.aw.valid'
        'axi.ar'
            'axi.ar.addr'
            'axi.ar.ready'
            'axi.ar.valid'
        'axi.w'
            'axi.w.data'
            'axi.w.strb'
            'axi.w.ready'
            'axi.w.valid'
        'axi.r'
            'axi.r.data'
            'axi.r.resp'
            'axi.r.ready'
            'axi.r.valid'
        'axi.b'
            'axi.b.resp'
            'axi.b.ready'
            'axi.b.valid'
    p2:'axi'
        'axi.aw'
            'axi.aw.addr'
            'axi.aw.ready'
            'axi.aw.valid'
        'axi.ar'
            'axi.ar.addr'
            'axi.ar.ready'
            'axi.ar.valid'
        'axi.w'
            'axi.w.data'
            'axi.w.strb'
            'axi.w.ready'
            'axi.w.valid'
        'axi.r'
            'axi.r.data'
            'axi.r.resp'
            'axi.r.ready'
            'axi.r.valid'
        'axi.b'
            'axi.b.resp'
            'axi.b.ready'
            'axi.b.valid'
"""



clk_ag_str = """clk:<hwt.interfaces.agents.clk.OscilatorAgent object at 0x7f51335e5f60>
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

u_ag_str = """<hwt.interfaces.agents.clk.OscilatorAgent object at 0x7f2c812d4ef0>
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

class ExampleWithArrayAxiLite(EmptyUnit):
    def _declr(self):
        addClkRstn(self)
        self.axi = AxiLite(asArraySize=3)


class SimulatorUtilsTC(SimTestCase):
    def test_pprintInterface(self):
        u = ExampleWithArrayAxiLite()
        o = StringIO()
        self.prepareUnit(u)
        pprintInterface(u.clk, file=o)
        self.assertEqual(o.getvalue(), "'clk'\n")
        
        o = StringIO()
        pprintInterface(u.axi, file=o)
        self.assertEqual(o.getvalue(), axi_str)

    def test_pprintAgents(self):
        u = ExampleWithArrayAxiLite()
        pointerRe = re.compile("0x[a-f0-9]*")
        self.prepareUnit(u)
        self.doSim(1)
        
        o = StringIO()
        pprintAgents(u.clk, file=o)
        self.assertEmpty(pointerRe.sub(o.getvalue(), ""), pointerRe.sub(clk_ag_str, ""))
        
        o = StringIO()
        pprintAgents(u.axi, file=o)
        self.assertEmpty(pointerRe.sub(o.getvalue(), ""), pointerRe.sub(axi_ag_str, ""))
        
        o = StringIO()
        pprintAgents(u, file=o)
        self.assertEmpty(pointerRe.sub(o.getvalue(), ""), pointerRe.sub(u_ag_str, ""))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IpCorePackagerTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(SimulatorUtilsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
