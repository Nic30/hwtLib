#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.hwIO_map import HwIOObjMap
from hwt.hwIOs.std import HwIOBramPort_noClk, HwIODataVld, HwIORegCntrl, \
    HwIOVectSignal, HwIOSignal
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axiLite_comp.endpoint_test import addrGetter
from hwtLib.amba.axiLite_comp.sim.memSpaceMaster import AxiLiteMemSpaceMaster
from hwtLib.amba.constants import RESP_OKAY


class Loop(HwModule):
    """
    Simple loop for any interface
    """

    def __init__(self, interfaceCls):
        self.interfaceCls = interfaceCls
        super(Loop, self).__init__()

    @override
    def hwConfig(self):
        self.interfaceCls.hwConfig(self)

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            self.din = self.interfaceCls()
            self.dout = self.interfaceCls()._m()

    @override
    def hwImpl(self):
        self.dout(self.din)


class SigLoop(HwModule):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        self.din = HwIOVectSignal(self.DATA_WIDTH)
        self.dout = HwIOVectSignal(self.DATA_WIDTH)._m()

    @override
    def hwImpl(self):
        self.dout(self.din)


class TestHwModuleWithChilds(HwModule):
    """
    Container of AxiLiteEndpoint constructed by fromHwIOMap
    """

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.bus = Axi4Lite()

            self.signalLoop = SigLoop()
            self.signalIn = HwIOVectSignal(self.DATA_WIDTH)

            self.regCntrlLoop = Loop(HwIORegCntrl)
            self.regCntrlOut = HwIORegCntrl()._m()

            self.vldSyncedLoop = Loop(HwIODataVld)
            self.vldSyncedOut = HwIODataVld()._m()

        with self._hwParamsShared(exclude=({"ADDR_WIDTH"}, set())):
            self.bramLoop = Loop(HwIOBramPort_noClk)
            self.bramLoop.ADDR_WIDTH = 2

            self.bramOut = HwIOBramPort_noClk()._m()
            self.bramOut.ADDR_WIDTH = 2

    @override
    def hwImpl(self):
        self.signalLoop.din(self.signalIn)
        self.regCntrlOut(self.regCntrlLoop.dout)
        self.vldSyncedOut(self.vldSyncedLoop.dout)
        self.bramOut(self.bramLoop.dout)

        def configEp(ep):
            ep._updateHwParamsFrom(self)

        rltSig10 = self._sig("sig", HBits(self.DATA_WIDTH), def_val=10)
        interfaceMap = HwIOObjMap([
            (rltSig10, "rltSig10"),
            (self.signalLoop.dout, "signal"),
            (self.regCntrlLoop.din, "regCntrl"),
            (self.vldSyncedLoop.din, "vldSynced"),
            (self.bramLoop.din, "bram"),
            (HBits(self.DATA_WIDTH), None),
        ])

        axiLiteConv = AxiLiteEndpoint.fromHwIOMap(interfaceMap)
        axiLiteConv._updateHwParamsFrom(self)
        self.conv = axiLiteConv

        axiLiteConv.connectByInterfaceMap(interfaceMap)
        axiLiteConv.bus(self.bus)
        axiLiteConv.decoded.vldSynced.din(None)

        propagateClkRstn(self)


TestHwModuleWithChilds_add_space_str = """\
struct {
    <HBits, 32bits> rltSig10 // start:0x0(bit) 0x0(byte)
    <HBits, 32bits> signal // start:0x20(bit) 0x4(byte)
    <HBits, 32bits> regCntrl // start:0x40(bit) 0x8(byte)
    <HBits, 32bits> vldSynced // start:0x60(bit) 0xc(byte)
    <HBits, 32bits>[4] bram // start:0x80(bit) 0x10(byte)
    //<HBits, 32bits> empty space // start:0x100(bit) 0x20(byte)
}"""


class TestHwModuleWithArr(HwModule):
    """
    Container of AxiLiteEndpoint constructed by fromHwIOMap
    """

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.bus = Axi4Lite()

            self.regCntrlLoop0 = Loop(HwIORegCntrl)
            self.regCntrlOut0 = HwIORegCntrl()._m()

            self.regCntrlLoop1 = Loop(HwIORegCntrl)
            self.regCntrlOut1 = HwIORegCntrl()._m()

            self.regCntrlLoop2 = Loop(HwIORegCntrl)
            self.regCntrlOut2 = HwIORegCntrl()._m()

    @override
    def hwImpl(self):
        self.regCntrlOut0(self.regCntrlLoop0.dout)
        self.regCntrlOut1(self.regCntrlLoop1.dout)
        self.regCntrlOut2(self.regCntrlLoop2.dout)

        def configEp(ep):
            ep._updateHwParamsFrom(self)

        interfaceMap = HwIOObjMap([
                ([self.regCntrlLoop0.din,
                  self.regCntrlLoop1.din,
                  self.regCntrlLoop2.din,
                  ], "regCntrl"),
            ])

        axiLiteConv = AxiLiteEndpoint.fromHwIOMap(interfaceMap)
        axiLiteConv._updateHwParamsFrom(self)
        self.conv = axiLiteConv

        axiLiteConv.connectByInterfaceMap(interfaceMap)
        axiLiteConv.bus(self.bus)

        propagateClkRstn(self)


TestHwModuleWithArr_addr_space_str = """\
struct {
    <HBits, 32bits>[3] regCntrl // start:0x0(bit) 0x0(byte)
}"""


class AxiLiteEndpoint_fromInterfaceTC(SimTestCase):

    @override
    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def mkRegisterMap(self, u):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(u.bus, self.addrProbe.discovered)

    def randomizeAll(self):
        dut = self.dut
        for hwIO in dut._hwIOs:
            if dut not in (dut.clk, dut.rst_n, dut.bus)\
                    and not isinstance(hwIO, (HwIOBramPort_noClk, HwIODataVld, HwIOSignal)):
                self.randomize(hwIO)

        self.randomize(dut.bus.ar)
        self.randomize(dut.bus.aw)
        self.randomize(dut.bus.r)
        self.randomize(dut.bus.w)
        self.randomize(dut.bus.b)

    def mySetUp(self, data_width=32):
        dut = self.dut = TestHwModuleWithChilds()

        self.DATA_WIDTH = data_width
        dut.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.dut, onAfterToRtl=self.mkRegisterMap)
        return dut

    def test_nop(self):
        dut = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(dut.bus._ag.r.data)
        self.assertEmpty(dut.bus._ag.b.data)
        self.assertEmpty(dut.regCntrlOut._ag.dout)
        self.assertEmpty(dut.vldSyncedOut._ag.data)
        self.assertEqual(dut.bramOut._ag.mem, {})

    def test_read(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        r.rltSig10.read()

        dut.signalIn._ag.data.append(MAGIC)
        r.signal.read()

        dut.regCntrlOut._ag.din.extend([MAGIC + 1])
        r.regCntrl.read()
        r.vldSynced.read()

        for i in range(4):
            dut.bramOut._ag.mem[i] = MAGIC + 2 + i
            r.bram[i].read()

        self.randomizeAll()
        self.runSim(600 * Time.ns)

        self.assertValSequenceEqual(
            dut.bus.r._ag.data, [
                (10, RESP_OKAY),
                (MAGIC, RESP_OKAY),
                (MAGIC + 1, RESP_OKAY),
                (None, RESP_OKAY), ] + [
                (MAGIC + 2 + i, RESP_OKAY)
                for i in range(4)
            ])

    def test_write(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        r.regCntrl.write(MAGIC)
        r.vldSynced.write(MAGIC + 1)
        for i in range(4):
            r.bram[i].write(MAGIC + 2 + i)

        self.randomizeAll()
        self.runSim(800 * Time.ns)

        self.assertValSequenceEqual(dut.regCntrlOut._ag.dout,
                                    [MAGIC, ])
        self.assertValSequenceEqual(dut.vldSyncedOut._ag.data,
                                    [MAGIC + 1, ])
        self.assertValSequenceEqual(dut.bus.b._ag.data, [RESP_OKAY for _ in range(6)])

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, TestHwModuleWithChilds_add_space_str)


class AxiLiteEndpoint_fromInterface_arr_TC(AxiLiteEndpoint_fromInterfaceTC):

    @override
    def mySetUp(self, data_width=32):
        dut = self.dut = TestHwModuleWithArr()

        self.DATA_WIDTH = data_width
        dut.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.dut, onAfterToRtl=self.mkRegisterMap)
        return dut

    def test_nop(self):
        dut = self.mySetUp(32)

        self.randomizeAll()
        self.runSim(100 * Time.ns)

        self.assertEmpty(dut.bus._ag.r.data)
        self.assertEmpty(dut.bus._ag.b.data)
        self.assertEmpty(dut.regCntrlOut0._ag.dout)
        self.assertEmpty(dut.regCntrlOut1._ag.dout)
        self.assertEmpty(dut.regCntrlOut2._ag.dout)

    def test_read(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        dut.regCntrlOut0._ag.din.extend([MAGIC])
        r.regCntrl[0].read()

        dut.regCntrlOut1._ag.din.extend([MAGIC + 1])
        r.regCntrl[1].read()

        dut.regCntrlOut2._ag.din.extend([MAGIC + 2])
        r.regCntrl[2].read()

        self.randomizeAll()
        self.runSim(600 * Time.ns)

        self.assertValSequenceEqual(
            dut.bus.r._ag.data, [
                (MAGIC, RESP_OKAY),
                (MAGIC + 1, RESP_OKAY),
                (MAGIC + 2, RESP_OKAY)
            ])

    def test_write(self):
        dut = self.mySetUp(32)
        MAGIC = 100
        r = self.regs

        for i in range(3):
            r.regCntrl[i].write(MAGIC + i)

        self.randomizeAll()
        self.runSim(800 * Time.ns)

        for i in range(3):
            hwIO = getattr(dut, f"regCntrlOut{i:d}")
            self.assertValSequenceEqual(hwIO._ag.dout,
                                        [MAGIC + i, ])
        self.assertValSequenceEqual(
            dut.bus.b._ag.data,
            [RESP_OKAY for _ in range(3)])

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        self.assertEqual(s, TestHwModuleWithArr_addr_space_str)


if __name__ == "__main__":
    import unittest
    _ALL_TCs = [AxiLiteEndpoint_fromInterfaceTC, AxiLiteEndpoint_fromInterface_arr_TC]

    testLoader = unittest.TestLoader()
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
