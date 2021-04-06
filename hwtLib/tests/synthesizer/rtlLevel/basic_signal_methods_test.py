import unittest

from hwt.code import If
from hwt.hdl.statements.assignmentContainer import HdlAssignmentContainer
from hwt.hdl.types.defs import BIT
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.indexOps import IndexOps
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr


class BasicSignalMethodsTC(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist()

    def test_signalPropertyTypes(self):
        a = self.n.sig("a")
        self.assertEqual(a.def_val.vld_mask, 0)

    def test_opRisingEdgeMultipletimesSameObj(self):
        clk = self.n.sig("ap_clk")
        self.assertEqual(clk._onRisingEdge(), clk._onRisingEdge())

    def test_syncSig(self):
        n = self.n
        clk = n.sig("ap_clk")
        a = n.sig("a", clk=clk)

        self.assertEqual(len(a.drivers), 1)
        _if = a.drivers[0]
        self.assertIsInstance(_if, If)

        self.assertEqual(len(_if.ifTrue), 1)
        self.assertEqual(_if.ifFalse, None)
        self.assertEqual(len(_if.elIfs), 0)

        assig = _if.ifTrue[0]
        self.assertEqual(assig.src, a.next)
        self.assertEqual(assig.dst, a)

        self.assertIs(_if.cond, clk._onRisingEdge())

    def test_syncSigWithReset(self):
        c = self.n
        clk = c.sig("ap_clk")
        rst = c.sig("ap_rst")
        a = c.sig("a", clk=clk, syncRst=rst, def_val=0)

        self.assertEqual(len(a.drivers), 1)

        _if = a.drivers[0]
        self.assertIsInstance(_if, If)

        self.assertIs(_if.cond, clk._onRisingEdge())
        self.assertEqual(len(_if.ifTrue), 1)
        self.assertEqual(_if.ifFalse, None)
        self.assertEqual(len(_if.elIfs), 0)

        if_reset = _if.ifTrue[0]

        self.assertIs(if_reset.cond, rst._isOn())
        self.assertEqual(len(if_reset.ifTrue), 1)
        self.assertEqual(len(if_reset.ifFalse), 1)
        self.assertEqual(len(if_reset.elIfs), 0)

        a_reset = if_reset.ifTrue[0]
        a_next = if_reset.ifFalse[0]
        self.assertIsInstance(a_reset, HdlAssignmentContainer)
        self.assertEqual(a_reset.src, BIT.from_py(0))

        self.assertIsInstance(a_next, HdlAssignmentContainer)
        self.assertEqual(a_next.src, a.next)

    def test_indexOps(self):
        c, interf = IndexOps()
        s = netlistToVhdlStr("IndexOps", c, interf)
        self.assertNotIn("sig_", s)


if __name__ == '__main__':
    unittest.main()
