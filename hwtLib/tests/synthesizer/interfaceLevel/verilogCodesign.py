import unittest

from hdl_toolkit.hdlObjects.typeShortcuts import hInt
from hdl_toolkit.synthesizer.interfaceLevel.unitFromHdl import UnitFromHdl
from hwtLib.tests.synthesizer.interfaceLevel.baseSynthesizerTC import BaseSynthesizerTC


ILVL_V = '../../../samples/verilogCodesign/verilog/'

class VerilogCodesignTC(BaseSynthesizerTC):
    def test_TernOpInModul(self):
        class TernOpInModulSample(UnitFromHdl):
            _hdlSources = ILVL_V + "ternOpInModul.v"
            _debugParser=True
                    
        u = TernOpInModulSample()
        u._loadDeclarations()
        
        self.assertEquals(u.a._dtype.bit_length(), 8)
        self.assertEquals(u.b._dtype.bit_length(), 1)
        
        u.CONDP.set(hInt(1))
        self.assertEquals(u.a._dtype.bit_length(), 4)
        self.assertEquals(u.b._dtype.bit_length(), 2)
        
    def test_SizeExpressions(self):
        class SizeExpressionsSample(UnitFromHdl):
            _hdlSources = ILVL_V + "sizeExpressions.v"        
        u = SizeExpressionsSample()
        u._loadDeclarations()
        
        A = u.paramA.get()
        B = u.paramB.get()
        self.assertEqual(u.portA._dtype.bit_length(), A.val)
        self.assertEqual(u.portB._dtype.bit_length(), A.val)
        self.assertEqual(u.portC._dtype.bit_length(), A.val // 8)
        self.assertEqual(u.portD._dtype.bit_length(), (A.val // 8) * 13)
        self.assertEqual(u.portE._dtype.bit_length(), B.val * (A.val // 8))
        self.assertEqual(u.portF._dtype.bit_length(), B.val * A.val)
        self.assertEqual(u.portG._dtype.bit_length(), B.val * (A.val - 4))
    
    def test_InterfaceArray(self):
        class InterfaceArraySample(UnitFromHdl):
            _hdlSources = ILVL_V + "interfaceArrayAxiStream.v"        
        u = InterfaceArraySample()
        u._loadDeclarations()
        
        self.assertEqual(u.input_axis.DATA_WIDTH.get().val, 32)
        self.assertEqual(u.input_axis._multipliedBy, u.LEN)
    
    
    def test_InterfaceArray2(self):
        class InterfaceArraySample(UnitFromHdl):
            _hdlSources = ILVL_V + "interfaceArrayAxi4.v"        
        u = InterfaceArraySample()
        u._loadDeclarations()
        
        self.assertEqual(u.m_axi._multipliedBy, u.C_NUM_MASTER_SLOTS)
        self.assertEqual(u.s_axi._multipliedBy, u.C_NUM_SLAVE_SLOTS)
    
    def test_paramSpecifiedByParam(self):
        class U(UnitFromHdl):
            _hdlSources = ILVL_V + "parameterSizeFromParameter.v"        
        u = U()
        u._loadDeclarations()
        
        self.assertEqual(u.A.get(), hInt(1))
        self.assertEqual(u.B.get(), hInt(2))
        
        
        self.assertEqual(u.aMultBMult64._dtype.bit_length(), 1*2*64)
        self.assertEqual(u.aMult32._dtype.bit_length(), 1*32)
        
    
    def test_axiCrossbar(self):
        class U(UnitFromHdl):
            _hdlSources = ILVL_V + "axiCrossbar.v"
        u = U()
        u._loadDeclarations()
        
        self.assertEqual(u.s_axi._multipliedBy, u.C_NUM_SLAVE_SLOTS)
        self.assertEqual(u.m_axi._multipliedBy, u.C_NUM_MASTER_SLOTS)
        
    
if __name__ == '__main__':
    suite = unittest.TestSuite()
    #suite.addTest(VerilogCodesignTC('test_InterfaceArray2'))
    suite.addTest(unittest.makeSuite(VerilogCodesignTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
