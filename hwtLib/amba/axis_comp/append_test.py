from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.append import AxiS_append


class AxiS_append_TC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u = AxiS_append(AxiStream)
        u.DATA_WIDTH.set(64)
        self.prepareUnit(u)

    def test_passSingleFrame1word(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.dataIn0._ag.data.append((MAGIC, m, 1))
        self.doSim(100 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 1)])
    
    def test_passDupletFrame1word(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.dataIn0._ag.data.append((MAGIC, m, 1))
        u.dataIn1._ag.data.append((MAGIC + 1, m, 1))
        self.doSim(100 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 1),
                                     (MAGIC + 1, m, 1)])

    def test_passDupletFrame3word(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        f0 = [(MAGIC, m, 0), (MAGIC + 1, m, 0), (MAGIC + 2, m, 1)]
        f1 = [(MAGIC + 3, m, 0), (MAGIC + 4, m, 0), (MAGIC + 5, m, 1)]
        u.dataIn0._ag.data.extend(f0)
        u.dataIn1._ag.data.extend(f1)
        self.doSim(100 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    f0 + f1)   

    def test_pass2xDupletFrame1word(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.dataIn0._ag.data.extend([(MAGIC, m, 1), (MAGIC + 1, m, 1)])
        u.dataIn1._ag.data.extend([(MAGIC + 2, m, 1), (MAGIC + 3, m, 1)])
        self.doSim(100 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 1),
                                     (MAGIC + 2, m, 1),
                                     (MAGIC + 1, m, 1),
                                     (MAGIC + 3, m, 1)])
    
    
if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(StructWriter_TC('test_doubleField'))
    suite.addTest(unittest.makeSuite(AxiS_append_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
