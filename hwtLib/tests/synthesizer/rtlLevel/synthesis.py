#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.assignment import Assignment
from hwt.hdlObjects.operatorDefs import AllOps
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.samples.rtlLvl.indexOps import IndexOps


class TestCaseSynthesis(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist()

    def test_opRisingEdgeMultipletimesSameObj(self):
        clk = self.n.sig("ap_clk")
        self.assertEqual(clk._onRisingEdge(), clk._onRisingEdge())
    
    
    def test_syncSig(self):
        n = self.n
        clk = n.sig("ap_clk")
        a = n.sig("a", clk=clk)
        self.assertEqual(len(a.drivers), 1)
        assig = next(iter(a.drivers))
        self.assertIsInstance(assig, Assignment)
        self.assertEqual(len(assig.cond), 1)
        self.assertEqual(assig.src, a.next)
        self.assertEqual(assig.dst , a)
        onRisE = assig.cond.pop()
        self.assertEqual(onRisE.origin.operator, AllOps.RISING_EDGE)
        self.assertEqual(onRisE.origin.ops[0], clk)
    
    def test_syncSigWithReset(self):
        c = self.n
        clk = c.sig("ap_clk")
        rst = c.sig("ap_rst")
        a = c.sig("a", clk=clk, syncRst=rst, defVal=0)
        self.assertEqual(len(a.drivers), 2)
        d_it = iter(sorted(list(a.drivers), key=lambda o: id(o))) 
        a_reset = next(d_it)
        a_next = next(d_it)
        self.assertIsInstance(a_reset, Assignment)
        self.assertIsInstance(a_next, Assignment)
        
        # [TODO] not eq operator is diffrent object 
        # self.assertEqual(a_reset.cond, {clk.opOnRisigEdge(), rst})
        # self.assertEqual(a_reset.src, 0)
        # self.assertEqual(a_next.cond, {clk.opOnRisigEdge(), rst.opNot()})
        # self.assertEqual(a_next.src, a.next)
        

    def test_indexOps(self):
        c, interf = IndexOps()
        _, arch = list(c.synthesize("indexOps", interf))

        s = VhdlSerializer.Architecture(arch, VhdlSerializer.getBaseNameScope())
        
        self.assertNotIn("sig_", s)
        

if __name__ == '__main__':
    unittest.main()
