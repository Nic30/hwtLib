#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdlConvertorAst.translate.common.name_scope import NameScope
from hwt.constants import DIRECTION, INTF_DIRECTION
from hwt.hwIOs.std import HwIOSignal
from hwt.pyUtils.arrayQuery import where
from hwtLib.abstract.emptyHwModule import EmptyHwModule
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi4s_fullduplex import Axi4StreamFullDuplex
from hwtLib.tests.synthesizer.interfaceLevel.baseSynthesizerTC import \
    BaseSynthesizerTC
from hwtLib.tests.synthesizer.interfaceLevel.subHwModuleSynthesisTC import synthesised


D = DIRECTION


def createTwoAxiDuplexStreams():
    i = Axi4StreamFullDuplex()
    i._name = 'i'
    i._loadDeclarations()
    i._setDirectionsLikeIn(INTF_DIRECTION.MASTER)

    i2 = Axi4StreamFullDuplex()
    i2._name = 'i2'
    i2._loadDeclarations()
    i2._setDirectionsLikeIn(INTF_DIRECTION.SLAVE)
    ns = NameScope(None, "", False)
    n = RtlNetlist()
    for _i in [i, i2]:
        _i._signalsForHwIO(n, None, ns)
    return i, i2


class HwIOSynthesizerTC(BaseSynthesizerTC):
    def test_SimpleHwModule2_iLvl(self):
        """
        Check interface directions pre and after synthesis
        """
        from hwtLib.examples.simpleHwModuleAxi4Stream import SimpleHwModuleAxi4Stream
        dut = SimpleHwModuleAxi4Stream()
        dut._loadDeclarations()
        m = self.assertIsM
        s = self.assertIsS

        # dut.a._resolveDirections()
        # dut.b._resolveDirections()
        #
        #
        # # inside
        # m(dut.a)
        # m(dut.a.data)
        # m(dut.a.last)
        # s(dut.a.ready)
        # m(dut.a.valid)
        # m(dut.a.strb)
        #
        # # inside
        # m(dut.b)
        # m(dut.b.data)
        # m(dut.b.last)
        # s(dut.b.ready)
        # m(dut.b.valid)
        # m(dut.b.strb)

        dut = synthesised(dut)

        # outside
        s(dut.a)
        s(dut.a.data)
        s(dut.a.last)
        m(dut.a.ready)
        s(dut.a.valid)
        s(dut.a.strb)

        m(dut.b)
        m(dut.b.data)
        m(dut.b.last)
        s(dut.b.ready)
        m(dut.b.valid)
        m(dut.b.strb)

    def test_SimpleHwModule2(self):
        from hwtLib.examples.simpleHwModuleAxi4Stream import SimpleHwModuleAxi4Stream
        dut = SimpleHwModuleAxi4Stream()
        dut._loadDeclarations()

        def ex(i): return self.assertTrue(i._isExtern)

        ex(dut.a)
        ex(dut.a.data)
        ex(dut.a.last)
        ex(dut.a.ready)
        ex(dut.a.strb)
        ex(dut.a.valid)
        ex(dut.b)
        ex(dut.b.data)
        ex(dut.b.last)
        ex(dut.b.ready)
        ex(dut.b.strb)
        ex(dut.b.valid)

        dut = synthesised(dut)

        for pn in ['a_data', 'a_last', 'a_strb', 'a_valid', 'b_ready']:
            self.assertDirIn(dut, pn)
        for pn in ['a_ready', 'b_data', 'b_last', 'b_strb', 'b_valid']:
            self.assertDirOut(dut, pn)

    def test_SimpleSubHwModule2(self):
        from hwtLib.examples.hierarchy.simpleSubHwModule2 import SimpleSubHwModule2
        dut = SimpleSubHwModule2()
        dut = synthesised(dut)

        for pn in ['a0_data', 'a0_last', 'a0_strb', 'a0_valid', 'b0_ready']:
            self.assertDirIn(dut, pn)
        for pn in ['a0_ready', 'b0_data', 'b0_last', 'b0_strb', 'b0_valid']:
            self.assertDirOut(dut, pn)

    def test_signalInstances(self):
        from hwtLib.examples.simpleHwModule import SimpleHwModule
        bram = SimpleHwModule()
        bram = synthesised(bram)

        self.assertIsNot(bram.a, bram.b, 'instances are properly instantiated')

        port_a = list(where(bram._ctx.hwModDec.ports, lambda x: x.name == "a"))
        port_b = list(where(bram._ctx.hwModDec.ports, lambda x: x.name == "b"))

        self.assertEqual(len(port_a), 1, 'entity has single port a')
        port_a = port_a[0]
        self.assertEqual(len(port_b), 1, 'entity has single port b')
        port_b = port_b[0]

        self.assertEqual(len(bram._ctx.hwModDec.ports), 2,
                         'entity has right number of ports')

        self.assertEqual(port_a.direction, D.IN,
                         'port a has src that means it should be input')
        self.assertEqual(port_b.direction, D.OUT,
                         'port b has no src that means it should be output')

    def test_EmptyHwModule(self):
        class Em(EmptyHwModule):
            def _declr(self):
                self.a = HwIOSignal()
                self.b = HwIOSignal()._m()

        dut = Em()
        dut = synthesised(dut)

        e = dut._ctx.hwModDec
        a = self.getPort(e, 'a')
        b = self.getPort(e, 'b')
        self.assertEqual(a.direction, D.IN)
        self.assertEqual(b.direction, D.OUT)

    def test_EmptyHwModuleWithCompositePort(self):
        class Dummy(EmptyHwModule):
            def _declr(self):
                self.a = Axi4()
                self.b = Axi4()._m()

        dut = Dummy()

        dut = synthesised(dut)
        self.assertTrue(dut.a.ar.addr._isExtern)
        e = dut._ctx.hwModDec

        a_ar_addr = self.getPort(e, 'a_ar_addr')
        self.assertEqual(a_ar_addr.direction, D.IN)

        a_ar_ready = self.getPort(e, 'a_ar_ready')
        self.assertEqual(a_ar_ready.direction, D.OUT)

        b_ar_addr = self.getPort(e, 'b_ar_addr')
        self.assertEqual(b_ar_addr.direction, D.OUT)

        b_ar_ready = self.getPort(e, "b_ar_ready")
        self.assertEqual(b_ar_ready.direction, D.IN)

    def test_IntfDirections_multistream(self):
        def s(i): return self.assertEqual(i._direction, INTF_DIRECTION.SLAVE)

        def m(i): return self.assertEqual(i._direction, INTF_DIRECTION.MASTER)

        i = Axi4StreamFullDuplex()
        i._loadDeclarations()
        self.assertRaises(Exception, i._reverseDirection)
        i._setDirectionsLikeIn(INTF_DIRECTION.MASTER)

        s(i.rx)
        s(i.rx.data)
        s(i.rx.last)
        s(i.rx.valid)
        m(i.rx.ready)

        m(i.tx)
        m(i.tx.data)
        m(i.tx.last)
        m(i.tx.valid)
        s(i.tx.ready)

    def test_IntfDirections_multistream_setSrc(self):
        def m(i): return self.assertEqual(i._direction, INTF_DIRECTION.MASTER)

        def s(i): return self.assertEqual(i._direction, INTF_DIRECTION.SLAVE)

        i, i2 = createTwoAxiDuplexStreams()

        i2(i)

        m(i)

        s(i.rx.data)
        s(i.rx.last)
        s(i.rx.valid)
        m(i.rx.ready)

        m(i.tx.data)
        m(i.tx.last)
        m(i.tx.valid)
        s(i.tx.ready)

        m(i2.rx.data)
        m(i2.rx.last)
        m(i2.rx.valid)
        s(i2.rx.ready)

        s(i2.tx.data)
        s(i2.tx.last)
        s(i2.tx.valid)
        m(i2.tx.ready)

    def test_IntfDirections_multistream_setSrc2(self):
        def m(i): return self.assertEqual(i._direction, INTF_DIRECTION.MASTER)

        def s(i): return self.assertEqual(i._direction, INTF_DIRECTION.SLAVE)

        i, i2 = createTwoAxiDuplexStreams()

        i.rx(i2.rx)
        i2.tx(i.tx)

        m(i)
        s(i.rx)
        s(i.rx.data)
        s(i.rx.last)
        s(i.rx.valid)
        m(i.rx.ready)

        m(i.tx.data)
        m(i.tx.last)
        m(i.tx.valid)
        s(i.tx.ready)

        s(i2)
        m(i2.rx.data)
        m(i2.rx.last)
        m(i2.rx.valid)
        s(i2.rx.ready)

        s(i2.tx.data)
        s(i2.tx.last)
        s(i2.tx.valid)
        m(i2.tx.ready)

        i._reverseDirection()
        i2._reverseDirection()

        s(i)
        m(i.rx)
        m(i.rx.data)
        m(i.rx.last)
        m(i.rx.valid)
        s(i.rx.ready)

        s(i.tx.data)
        s(i.tx.last)
        s(i.tx.valid)
        m(i.tx.ready)

        m(i2)
        s(i2.rx.data)
        s(i2.rx.last)
        s(i2.rx.valid)
        m(i2.rx.ready)

        m(i2.tx.data)
        m(i2.tx.last)
        m(i2.tx.valid)
        s(i2.tx.ready)


if __name__ == '__main__':
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HwIOSynthesizerTC("test_IntfDirections_multistream_setSrc")])
    suite = testLoader.loadTestsFromTestCase(HwIOSynthesizerTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
