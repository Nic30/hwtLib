#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import DIRECTION
from hwt.hdlObjects.typeShortcuts import vecT, hInt
from hwt.interfaces.std import Signal
from hwt.synthesizer.exceptions import TypeConversionErr
from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit, setOut
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.shortcuts import toRtl, synthesised
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.fullDuplexAxiStream import FullDuplexAxiStream 
from hwtLib.samples.iLvl.hierarchy.unitToUnitConnection import UnitToUnitConnection
from hwtLib.samples.iLvl.simple2withNonDirectIntConnection import Simple2withNonDirectIntConnection
from hwtLib.tests.synthesizer.interfaceLevel.baseSynthesizerTC import BaseSynthesizerTC


D = DIRECTION


class UnitWithArrIntf(EmptyUnit):
    def _config(self):
        self.DATA_WIDTH = Param(64)
    def _declr(self):
        with self._paramsShared():
            self.a = AxiStream()
            self.b = AxiStream(multipliedBy=hInt(2))
        
    def _impl(self):
        setOut(self.b)
    
class UnitWithArrIntfParent(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(64)
    
    def _declr(self):
        with self._paramsShared():
            self.a = AxiStream()
            self.b0 = AxiStream()
            self.b1 = AxiStream()
        
            self.u0 = UnitWithArrIntf()
    
    def _impl(self):
        self.u0.a ** self.a
        self.b0 ** self.u0.b[0]
        self.b1 ** self.u0.b[1] 

class SubunitsSynthesisTC(BaseSynthesizerTC):
    def test_GroupOfBlockrams(self):
        """
        Check interface directions pre and after synthesis
        """
        from hwtLib.samples.iLvl.hierarchy.groupOfBlockrams import GroupOfBlockrams
        u = GroupOfBlockrams()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(len(u._architecture.componentInstances), 2)

    def test_SubunitWithWrongDataT(self):
        class InternUnit(Unit):
            def _declr(self):
                dt = vecT(64)
                self.a = Signal(dtype=dt)
                self.b = Signal(dtype=dt)
            
            def _impl(self):
                self.b ** self.a
                

        class OuterUnit(Unit):
            def _declr(self):
                dt = vecT(32)
                self.a = Signal(dtype=dt)
                self.b = Signal(dtype=dt)
                self.iu = InternUnit()

            def _impl(self):
                self.iu.a ** self.a 
                self.b ** self.iu.b 

        self.assertRaises(TypeConversionErr, lambda : toRtl(OuterUnit))
        
    def test_twoSubUnits(self):
        u = UnitToUnitConnection()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(len(u._architecture.componentInstances), 2)
        
    def test_threeSubUnits(self):
        class ThreeSubunits(Unit):
            """a -> u0 -> u1 -> u2 -> b"""
            def _config(self):
                self.DATA_WIDTH = Param(64)
            def _declr(self):
                with self._paramsShared():
                    self.a = AxiStream()
                    self.b = AxiStream()
                
                    self.u0 = Simple2withNonDirectIntConnection()
                    self.u1 = Simple2withNonDirectIntConnection()
                    self.u2 = Simple2withNonDirectIntConnection()
                
            def _impl(self):
                self.u0.a ** self.a
                self.u1.a ** self.u0.c 
                self.u2.a ** self.u1.c 
                self.b ** self.u2.c 
        
        u = ThreeSubunits()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(len(u._architecture.componentInstances), 3)

    def test_subUnitWithArrIntf(self):
        u = UnitWithArrIntfParent()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(len(u._architecture.componentInstances), 1)
    
    def test_threeLvlSubUnitsArrIntf(self):
        class ThreeSubunits(Unit):
            """a -> u0 -> u1 -> u2 -> b"""
            def _config(self):
                self.DATA_WIDTH = Param(64)
            def _declr(self):
                with self._paramsShared():
                    self.a = AxiStream()
                    self.b0 = AxiStream()
                    self.b1 = AxiStream()
                    
                    self.u0 = Simple2withNonDirectIntConnection()
                    self.u1 = UnitWithArrIntf()
                    self.u2_0 = Simple2withNonDirectIntConnection()
                    self.u2_1 = Simple2withNonDirectIntConnection()
                
            def _impl(self):
                self.u0.a ** self.a
                self.u1.a ** self.u0.c
                                 
                self.u2_0.a ** self.u1.b[0]
                self.u2_1.a ** self.u1.b[1] 
                
                self.b0 ** self.u2_0.c     
                self.b1 ** self.u2_1.c
  
        u = ThreeSubunits()
        u._loadDeclarations()
        u = synthesised(u)
        self.assertEqual(len(u._architecture.componentInstances), 4)

    def test_unitWithIntfPartsConnectedSeparately(self):
        class FDStreamConnection(Unit):
            def _declr(self):
                self.dataIn = FullDuplexAxiStream()
                self.dataOut = FullDuplexAxiStream()
            def _impl(self):
                self.dataOut.tx ** self.dataIn.tx
                self.dataIn.rx ** self.dataOut.rx 

        u = FDStreamConnection()
        u._loadDeclarations()
        u = synthesised(u)        

if __name__ == '__main__':
    
    # print(toRtl(UnitWithArrIntfParent))
    
    suite = unittest.TestSuite()
    # suite.addTest(SubunitsSynthesisTC('test_subUnitWithArrIntf'))
    suite.addTest(unittest.makeSuite(SubunitsSynthesisTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

