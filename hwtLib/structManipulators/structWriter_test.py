import unittest

from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.struct import HStruct
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.structManipulators.structWriter import StructWriter
from hwtLib.types.ctypes import uint64_t


class StructWriter_TC(SimTestCase):
    def buildEnv(self, structT):
        u = self.u = StructWriter(structT)
        u.DATA_WIDTH.set(64)
        self.prepareUnit(u)
        m = DenseMemory(evalParam(u.DATA_WIDTH).val, u.clk, wDatapumpIntf=u.wDatapump)
        return m

    def test_singleField(self):
        MAGIC = 54
        MAGIC2 = 0x1000
        s = HStruct(
                    (uint64_t, "field0")
                   )

        m = self.buildEnv(s)
        self.u.field0._ag.data.append(MAGIC)
        self.u.set._ag.data.append(MAGIC2)
        self.doSim(100 * Time.ns)

        s_got = m.getStruct(MAGIC2, s)
        self.assertValEqual(s_got.field0, MAGIC)

    def test_doubleField(self):
        MAGIC = 54
        MAGIC2 = 0x1000
        s = HStruct(
                    (uint64_t, "field0"),
                    (uint64_t, "field1")
                   )

        m = self.buildEnv(s)
        self.u.field0._ag.data.append(MAGIC)
        self.u.field1._ag.data.append(MAGIC+1)
        self.u.set._ag.data.append(MAGIC2)

        self.doSim(100 * Time.ns)

        self.assertEmpty(self.u.field0._ag.data)
        self.assertEmpty(self.u.field1._ag.data)
        self.assertEmpty(self.u.set._ag.data)

        s_got = m.getStruct(MAGIC2, s)
        self.assertValEqual(s_got.field0, MAGIC)
        self.assertValEqual(s_got.field1, MAGIC+1)

    def test_tripleField(self):
        MAGIC = 54
        MAGIC2 = 0x1000
        s = HStruct(
                     (uint64_t, "field0"),
                     (uint64_t, "field1"),
                     (uint64_t, "field2")
                     )

        m = self.buildEnv(s)
        self.u.field0._ag.data.append(MAGIC)
        self.u.field1._ag.data.append(MAGIC+1)
        self.u.field2._ag.data.append(MAGIC+2)
        self.u.set._ag.data.append(MAGIC2)

        self.doSim(100 * Time.ns)

        self.assertEmpty(self.u.field0._ag.data)
        self.assertEmpty(self.u.field1._ag.data)
        self.assertEmpty(self.u.field2._ag.data)
        self.assertEmpty(self.u.set._ag.data)

        s_got = m.getStruct(MAGIC2, s)
        self.assertValEqual(s_got.field0, MAGIC)
        self.assertValEqual(s_got.field1, MAGIC+1)
        self.assertValEqual(s_got.field2, MAGIC+2)

    def test_holeOnStart(self):
        MAGIC = 54
        MAGIC2 = 0x1000
        s = HStruct(
                    (uint64_t, None),
                    (uint64_t, None),
                    (uint64_t, None),
                    (uint64_t, None),
                    (uint64_t, "field0"),
                    (uint64_t, "field1"),
                    (uint64_t, "field2")
                   )

        m = self.buildEnv(s)
        self.u.field0._ag.data.append(MAGIC)
        self.u.field1._ag.data.append(MAGIC+1)
        self.u.field2._ag.data.append(MAGIC+2)
        self.u.set._ag.data.append(MAGIC2)

        self.doSim(100 * Time.ns)

        self.assertEmpty(self.u.field0._ag.data)
        self.assertEmpty(self.u.field1._ag.data)
        self.assertEmpty(self.u.field2._ag.data)
        self.assertEmpty(self.u.set._ag.data)

        s_got = m.getStruct(MAGIC2, s)
        self.assertValEqual(s_got.field0, MAGIC)
        self.assertValEqual(s_got.field1, MAGIC+1)
        self.assertValEqual(s_got.field2, MAGIC+2)


    def test_holeInMiddle(self):
        MAGIC = 54
        MAGIC2 = 0x1000
        s = HStruct(
                    (uint64_t, "field0"),
                    (uint64_t, None),
                    (uint64_t, None),
                    (uint64_t, None),
                    (uint64_t, None),
                    (uint64_t, "field1"),
                    (uint64_t, "field2")
                   )

        m = self.buildEnv(s)
        self.u.field0._ag.data.append(MAGIC)
        self.u.field1._ag.data.append(MAGIC+1)
        self.u.field2._ag.data.append(MAGIC+2)
        self.u.set._ag.data.append(MAGIC2)
        
        self.doSim(100 * Time.ns)

        self.assertEmpty(self.u.field0._ag.data)
        self.assertEmpty(self.u.field1._ag.data)
        self.assertEmpty(self.u.field2._ag.data)
        self.assertEmpty(self.u.set._ag.data)

        s_got = m.getStruct(MAGIC2, s)
        self.assertValEqual(s_got.field0, MAGIC)
        self.assertValEqual(s_got.field1, MAGIC+1)
        self.assertValEqual(s_got.field2, MAGIC+2)

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(StructWriter_TC('test_doubleField'))
    suite.addTest(unittest.makeSuite(StructWriter_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
