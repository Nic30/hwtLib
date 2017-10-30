#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.code import connect
from hwt.hdl.constants import DIRECTION, INTF_DIRECTION
from hwt.interfaces.std import Signal
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hwt.synthesizer.interfaceLevel.emptyUnit import setOut
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.fullDuplexAxiStream import FullDuplexAxiStream
from hwtLib.tests.synthesizer.interfaceLevel.baseSynthesizerTC import \
    BaseSynthesizerTC
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import synthesised


D = DIRECTION


def createTwoAxiDuplexStreams():
    i = FullDuplexAxiStream()
    i._name = 'i'
    i._loadDeclarations()

    i2 = FullDuplexAxiStream()
    i2._name = 'i2'
    i2._loadDeclarations()

    n = RtlNetlist()
    for _i in [i, i2]:
        _i._signalsForInterface(n)
    return i, i2


class InterfaceSynthesizerTC(BaseSynthesizerTC):
    def test_SimpleUnit2_iLvl(self):
        """
        Check interface directions pre and after synthesis
        """
        from hwtLib.samples.simpleAxiStream import SimpleUnitAxiStream
        u = SimpleUnitAxiStream()
        u._loadDeclarations()
        m = self.assertIsM
        s = self.assertIsS

        # u.a._resolveDirections()
        # u.b._resolveDirections()
        #
        #
        # # inside
        # m(u.a)
        # m(u.a.data)
        # m(u.a.last)
        # s(u.a.ready)
        # m(u.a.valid)
        # m(u.a.strb)
        #
        # # inside
        # m(u.b)
        # m(u.b.data)
        # m(u.b.last)
        # s(u.b.ready)
        # m(u.b.valid)
        # m(u.b.strb)

        u = synthesised(u)

        # outside
        s(u.a)
        s(u.a.data)
        s(u.a.last)
        m(u.a.ready)
        s(u.a.valid)
        s(u.a.strb)

        m(u.b)
        m(u.b.data)
        m(u.b.last)
        s(u.b.ready)
        m(u.b.valid)
        m(u.b.strb)

    def test_SimpleUnit2(self):
        from hwtLib.samples.simpleAxiStream import SimpleUnitAxiStream
        u = SimpleUnitAxiStream()
        u._loadDeclarations()

        def ex(i): return self.assertTrue(i._isExtern)

        ex(u.a)
        ex(u.a.data)
        ex(u.a.last)
        ex(u.a.ready)
        ex(u.a.strb)
        ex(u.a.valid)
        ex(u.b)
        ex(u.b.data)
        ex(u.b.last)
        ex(u.b.ready)
        ex(u.b.strb)
        ex(u.b.valid)

        u = synthesised(u)

        for pn in ['a_data', 'a_last', 'a_strb', 'a_valid', 'b_ready']:
            self.assertDirIn(u, pn)
        for pn in ['a_ready', 'b_data', 'b_last', 'b_strb', 'b_valid']:
            self.assertDirOut(u, pn)

    def test_SimpleSubUnit2(self):
        from hwtLib.samples.hierarchy.simpleSubunit2 import SimpleSubunit2
        u = SimpleSubunit2()
        u = synthesised(u)

        for pn in ['a0_data', 'a0_last', 'a0_strb', 'a0_valid', 'b0_ready']:
            self.assertDirIn(u, pn)
        for pn in ['a0_ready', 'b0_data', 'b0_last', 'b0_strb', 'b0_valid']:
            self.assertDirOut(u, pn)

    def test_signalInstances(self):
        from hwtLib.samples.simple import SimpleUnit
        bram = SimpleUnit()
        bram = synthesised(bram)

        self.assertIsNot(bram.a, bram.b, 'instances are properly instantiated')

        port_a = list(where(bram._entity.ports, lambda x: x.name == "a"))
        port_b = list(where(bram._entity.ports, lambda x: x.name == "b"))

        self.assertEqual(len(port_a), 1, 'entity has single port a')
        port_a = port_a[0]
        self.assertEqual(len(port_b), 1, 'entity has single port b')
        port_b = port_b[0]

        self.assertEqual(len(bram._entity.ports), 2,
                         'entity has right number of ports')

        self.assertEqual(port_a.direction, D.IN,
                         'port a has src that means it should be input')
        self.assertEqual(port_b.direction, D.OUT,
                         'port b has no src that means it should be output')

    def test_EmptyUnit(self):
        class Eu(EmptyUnit):
            def _declr(self):
                self.a = Signal()
                self.b = Signal()

            def _impl(self):
                setOut(self.b)

        u = Eu()
        u = synthesised(u)

        e = u._entity
        a = self.getPort(e, 'a')
        b = self.getPort(e, 'b')
        self.assertEqual(a.direction, D.IN)
        self.assertEqual(b.direction, D.OUT)

    def test_EmptyUnitWithCompositePort(self):
        class Dummy(EmptyUnit):
            def _declr(self):
                self.a = Axi4()
                self.b = Axi4()

            def _impl(self):
                setOut(self.b)

        u = Dummy()

        u = synthesised(u)
        self.assertTrue(u.a.ar.addr._isExtern)
        e = u._entity

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

        i = FullDuplexAxiStream()
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
        n = RtlNetlist()

        i._signalsForInterface(n)
        i2._signalsForInterface(n)

        connect(i, i2)
        i._resolveDirections()
        i2._resolveDirections()

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

        connect(i2.rx, i.rx)
        connect(i.tx, i2.tx)
        i._resolveDirections()
        i2._resolveDirections()

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
    suite = unittest.TestSuite()
    # suite.addTest(InterfaceSyntherisatorTC('test_IntfDirections_multistream_setSrc'))
    suite.addTest(unittest.makeSuite(InterfaceSynthesizerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
