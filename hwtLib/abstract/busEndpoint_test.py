import unittest
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwt.interfaces.std import RegCntrl, VectSignal, Signal, VldSynced

def regCntr(name, width):
    a = RegCntrl()
    a.DATA_WIDTH.set(width)
    a._name = name
    a._loadDeclarations()
    return a

def sig(name, width):
    a = VectSignal(width)
    a._name = name
    a._loadDeclarations()
    return a

def vldSynced(name, width):
    a = VldSynced()
    a.DATA_WIDTH.set(width)
    a._name = name
    a._loadDeclarations()
    return a

class BusEndpointTC(unittest.TestCase):
    def test_resolveRegStructFromIntfMap(self):
        prefix = "abc"
        DATA_WIDTH = 32
        
        fields = BusEndpoint._resolveRegStructFromIntfMap(
                    prefix=prefix,
                    interfaceMap=[
                        regCntr("a", DATA_WIDTH),
                        regCntr("b", DATA_WIDTH)
                        ],
                    DATA_WIDTH=DATA_WIDTH,
                    aliginFields=False)
        fields = list(fields)

        self.assertEqual(len(fields), 2)
        
        for f, name in zip(fields, ["a", "b"]):
            self.assertEqual(f[0].bit_length(), DATA_WIDTH)
            self.assertEqual(f[1], prefix + name)
            info = f[2]
            self.assertEqual(info.access, "rw")
            self.assertEqual(info.disolveArray, False)
            self.assertIsInstance(info.fieldInterface, (RegCntrl,))

    def test_resolveRegStructFromIntfMap_sig(self):
        prefix = "abc"
        DATA_WIDTH = 32
        
        fields = BusEndpoint._resolveRegStructFromIntfMap(
                    prefix=prefix,
                    interfaceMap=[
                        sig("a", DATA_WIDTH),
                        sig("b", DATA_WIDTH)
                        ],
                    DATA_WIDTH=DATA_WIDTH,
                    aliginFields=False)
        fields = list(fields)

        self.assertEqual(len(fields), 2)
        
        for f, name in zip(fields, ["a", "b"]):
            self.assertEqual(f[0].bit_length(), DATA_WIDTH)
            self.assertEqual(f[1], prefix + name)
            info = f[2]
            self.assertEqual(info.access, "r")
            self.assertEqual(info.disolveArray, False)
            self.assertIsInstance(info.fieldInterface, (Signal,))

    def test_resolveRegStructFromIntfMap_vldSynced(self):
        prefix = "abc"
        DATA_WIDTH = 32
        
        fields = BusEndpoint._resolveRegStructFromIntfMap(
                    prefix=prefix,
                    interfaceMap=[
                        vldSynced("a", DATA_WIDTH),
                        vldSynced("b", DATA_WIDTH)
                        ],
                    DATA_WIDTH=DATA_WIDTH,
                    aliginFields=False)
        fields = list(fields)

        self.assertEqual(len(fields), 2)
        
        for f, name in zip(fields, ["a", "b"]):
            self.assertEqual(f[0].bit_length(), DATA_WIDTH)
            self.assertEqual(f[1], prefix + name)
            info = f[2]
            self.assertEqual(info.access, "w")
            self.assertEqual(info.disolveArray, False)
            self.assertIsInstance(info.fieldInterface, (VldSynced))

    def test_resolveRegStructFromIntfMap_aligin(self):
        prefix = "abc"
        DATA_WIDTH = 32
        
        fields = BusEndpoint._resolveRegStructFromIntfMap(
                    prefix=prefix,
                    interfaceMap=[
                        regCntr("a", 8),
                        regCntr("b", 8)
                        ],
                    DATA_WIDTH=DATA_WIDTH,
                    aliginFields=True)
        fields = list(fields)
        self.assertEqual(len(fields), 4)
        
        for f, name, width in zip(fields, [None, "a", None, "b"], [32 - 8, 8, 32 - 8, 8]):
            self.assertEqual(f[0].bit_length(), width)
            if name is None:
                self.assertEqual(f[1], None)
                self.assertEqual(f[2], None)
            else:
                self.assertEqual(f[1], prefix + name)
                info = f[2]
                self.assertEqual(info.access, "rw")
                self.assertEqual(info.disolveArray, False)
                self.assertIsInstance(info.fieldInterface, (RegCntrl,))    
        

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiTC('test_axi_size'))
    suite.addTest(unittest.makeSuite(BusEndpointTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)        
