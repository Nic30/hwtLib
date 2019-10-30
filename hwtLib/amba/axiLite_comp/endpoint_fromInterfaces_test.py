#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.std import BramPort_withoutClk, VldSynced, RegCntrl, \
    VectSignal, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster
from hwt.hdl.types.bits import Bits
from hwtLib.amba.axiLite_comp.endpoint_test import addrGetter
from hwt.interfaces.structIntf import IntfMap


class Loop(Unit):
    """
    Simple loop for any interface
    """

    def __init__(self, interfaceCls):
        self.interfaceCls = interfaceCls
        super(Loop, self).__init__()

    def _config(self):
        self.interfaceCls._config(self)

    def _declr(self):
        with self._paramsShared():
            self.din = self.interfaceCls()
            self.dout = self.interfaceCls()._m()

    def _impl(self):
        self.dout(self.din)


class SigLoop(Unit):

    def _config(self):
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        self.din = VectSignal(self.DATA_WIDTH)
        self.dout = VectSignal(self.DATA_WIDTH)._m()

    def _impl(self):
        self.dout(self.din)


class TestUnittWithChilds(Unit):
    """
    Container of AxiLiteEndpoint constructed by fromInterfaceMap
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.bus = Axi4Lite()

            self.signalLoop = SigLoop()
            self.signalIn = VectSignal(self.DATA_WIDTH)

            self.regCntrlLoop = Loop(RegCntrl)
            self.regCntrlOut = RegCntrl()._m()

            self.vldSyncedLoop = Loop(VldSynced)
            self.vldSyncedOut = VldSynced()._m()

        with self._paramsShared(exclude=({"ADDR_WIDTH"}, set())):
            self.bramLoop = Loop(BramPort_withoutClk)
            self.bramLoop.ADDR_WIDTH = 2

            self.bramOut = BramPort_withoutClk()._m()
            self.bramOut.ADDR_WIDTH = 2

    def _impl(self):
        self.signalLoop.din(self.signalIn)
        self.regCntrlOut(self.regCntrlLoop.dout)
        self.vldSyncedOut(self.vldSyncedLoop.dout)
        self.bramOut(self.bramLoop.dout)

        def configEp(ep):
            ep._updateParamsFrom(self)

        rltSig10 = self._sig("sig", Bits(self.DATA_WIDTH), def_val=10)
        interfaceMap = IntfMap([
            (rltSig10, "rltSig10"),
            (self.signalLoop.dout, "signal"),
            (self.regCntrlLoop.din, "regCntrl"),
            (self.vldSyncedLoop.din, "vldSynced"),
            (self.bramLoop.din, "bram"),
            (Bits(self.DATA_WIDTH), None),
        ])

        axiLiteConv = AxiLiteEndpoint.fromInterfaceMap(interfaceMap)
        axiLiteConv._updateParamsFrom(self)
        self.conv = axiLiteConv

        axiLiteConv.connectByInterfaceMap(interfaceMap)
        axiLiteConv.bus(self.bus)
        axiLiteConv.decoded.vldSynced.din(None)

        propagateClkRstn(self)


TestUnittWithChilds_add_space_str = """\
struct {
    <Bits, 32bits> rltSig10 // start:0x0(bit) 0x0(byte)
    <Bits, 32bits, force_vector> signal // start:0x20(bit) 0x4(byte)
    <Bits, 32bits, force_vector> regCntrl // start:0x40(bit) 0x8(byte)
    <Bits, 32bits, force_vector> vldSynced // start:0x60(bit) 0xc(byte)
    <Bits, 32bits>[4] bram // start:0x80(bit) 0x10(byte)
    //<Bits, 32bits> empty space // start:0x100(bit) 0x20(byte)
}"""


class TestUnittWithArr(Unit):
    """
    Container of AxiLiteEndpoint constructed by fromInterfaceMap
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.bus = Axi4Lite()

            self.regCntrlLoop0 = Loop(RegCntrl)
            self.regCntrlOut0 = RegCntrl()._m()

            self.regCntrlLoop1 = Loop(RegCntrl)
            self.regCntrlOut1 = RegCntrl()._m()

            self.regCntrlLoop2 = Loop(RegCntrl)
            self.regCntrlOut2 = RegCntrl()._m()

    def _impl(self):
        self.regCntrlOut0(self.regCntrlLoop0.dout)
        self.regCntrlOut1(self.regCntrlLoop1.dout)
        self.regCntrlOut2(self.regCntrlLoop2.dout)

        def configEp(ep):
            ep._updateParamsFrom(self)

        interfaceMap = IntfMap([
                ([self.regCntrlLoop0.din,
                  self.regCntrlLoop1.din,
                  self.regCntrlLoop2.din,
                  ], "regCntrl"),
            ])

        axiLiteConv = AxiLiteEndpoint.fromInterfaceMap(interfaceMap)
        axiLiteConv._updateParamsFrom(self)
        self.conv = axiLiteConv

        axiLiteConv.connectByInterfaceMap(interfaceMap)
        axiLiteConv.bus(self.bus)

        propagateClkRstn(self)


TestUnittWithArr_addr_space_str = """\
struct {
    <Bits, 32bits, force_vector>[3] regCntrl // start:0x0(bit) 0x0(byte)
}"""


class AxiLiteEndpoint_fromInterfaceTC(SimTestCase):

    def mkRegisterMap(self, u):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(u.bus, self.addrProbe.discovered)

    def randomizeAll(self):
        u = self.u
        for intf in u._interfaces:
            if u not in (u.clk, u.rst_n, u.bus)\
                    and not isinstance(intf, (BramPort_withoutClk, VldSynced, Signal)):
                self.randomize(intf)

        self.randomize(u.bus.ar)
        self.randomize(u.bus.aw)
        self.randomize(u.bus.r)
        self.randomize(u.bus.w)
        self.randomize(u.bus.b)

    def mySetUp(self, data_width=32):
        u = self.u = TestUnittWithChilds()

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        self.assertEmpty(u.bus._ag.b.data)
        self.assertEmpty(u.regCntrlOut._ag.dout)
        self.assertEmpty(u.vldSyncedOut._ag.data)
        self.assertEqual(u.bramOut._ag.mem, {})

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        r.rltSig10.read()

        u.signalIn._ag.data.append(MAGIC)
        r.signal.read()

        u.regCntrlOut._ag.din.extend([MAGIC + 1])
        r.regCntrl.read()
        r.vldSynced.read()

        for i in range(4):
            u.bramOut._ag.mem[i] = MAGIC + 2 + i
            r.bram[i].read()

        self.randomizeAll()
        self.runSim(600 * Time.ns)

        self.assertValSequenceEqual(u.bus.r._ag.data,
                                    [(10, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (None, RESP_OKAY), ] + 
                                    [(MAGIC + 2 + i, RESP_OKAY) for i in range(4)])

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        r.regCntrl.write(MAGIC)
        r.vldSynced.write(MAGIC + 1)
        for i in range(4):
            r.bram[i].write(MAGIC + 2 + i)

        self.randomizeAll()
        self.runSim(800 * Time.ns)

        self.assertValSequenceEqual(u.regCntrlOut._ag.dout,
                                    [MAGIC, ])
        self.assertValSequenceEqual(u.vldSyncedOut._ag.data,
                                    [MAGIC + 1, ])
        self.assertValSequenceEqual(u.bus.b._ag.data, [RESP_OKAY for _ in range(6)])

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, TestUnittWithChilds_add_space_str)


class AxiLiteEndpoint_fromInterface_arr_TC(AxiLiteEndpoint_fromInterfaceTC):

    def mySetUp(self, data_width=32):
        u = self.u = TestUnittWithArr()

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        self.assertEmpty(u.bus._ag.b.data)
        self.assertEmpty(u.regCntrlOut0._ag.dout)
        self.assertEmpty(u.regCntrlOut1._ag.dout)
        self.assertEmpty(u.regCntrlOut2._ag.dout)

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        u.regCntrlOut0._ag.din.extend([MAGIC])
        r.regCntrl[0].read()

        u.regCntrlOut1._ag.din.extend([MAGIC + 1])
        r.regCntrl[1].read()

        u.regCntrlOut2._ag.din.extend([MAGIC + 2])
        r.regCntrl[2].read()

        self.randomizeAll()
        self.runSim(600 * Time.ns)

        self.assertValSequenceEqual(u.bus.r._ag.data,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC + 2, RESP_OKAY)
                                     ])

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        for i in range(3):
            r.regCntrl[i].write(MAGIC + i)

        self.randomizeAll()
        self.runSim(800 * Time.ns)

        for i in range(3):
            intf = getattr(u, "regCntrlOut%d" % i)
        self.assertValSequenceEqual(intf._ag.dout,
                                    [MAGIC + i, ])
        self.assertValSequenceEqual(u.bus.b._ag.data, [RESP_OKAY for _ in range(3)])

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, TestUnittWithArr_addr_space_str)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AxiLiteEndpoint_fromInterfaceTC('test_read'))
    suite.addTest(unittest.makeSuite(AxiLiteEndpoint_fromInterfaceTC))
    suite.addTest(unittest.makeSuite(AxiLiteEndpoint_fromInterface_arr_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
