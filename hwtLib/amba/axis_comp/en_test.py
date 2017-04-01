from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.en import AxiS_en


class AxiS_en_TC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u = AxiS_en(AxiStream)
        self.prepareUnit(u)

    def test_break(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.en._ag.data += [0]
        u.dataIn._ag.data.append((MAGIC, m, 1))
        self.doSim(100 * Time.ns)
        self.assertEmpty(u.dataOut._ag.data)

    def test_pass(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.en._ag.data += [1]
        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        u.dataIn._ag.data.extend(d)
        self.doSim(100 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, d)

    def test_passFirstBreakContinue(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.en._ag.data += [1, 0, 0, 0, 1]
        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        u.dataIn._ag.data.extend(d)
        self.doSim(100 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, d)

    def test_randomized(self):
        self.randomize(self.u.dataIn)
        self.randomize(self.u.dataOut)

        m = mask(64 // 8)
        MAGIC = 987
        u = self.u

        def en():
            while True:
                yield 1
                yield 0
        u.en._ag.data = en()
        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        u.dataIn._ag.data.extend(d)
        self.doSim(200 * len(d) * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, d)




if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(StructWriter_TC('test_doubleField'))
    suite.addTest(unittest.makeSuite(AxiS_en_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
