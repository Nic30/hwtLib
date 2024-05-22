import unittest

from hdlConvertorAst.hdlAst._structural import HdlModuleDec
from hwt.constants import INTF_DIRECTION, DIRECTION
from hwt.hwIO import HwIO
from hwt.hwModule import HwModule
from hwt.pyUtils.arrayQuery import single, NoValueExc


class BaseSynthesizerTC(unittest.TestCase):

    def assertIsM(self, hwIO: HwIO):
        self.assertEqual(hwIO._direction, INTF_DIRECTION.MASTER)

    def assertIsS(self, hwIO: HwIO):
        self.assertEqual(hwIO._direction, INTF_DIRECTION.SLAVE)

    def assertDir(self, dut: HwModule, portName: str, direction: DIRECTION):
        try:
            p = self.getPort(dut._ctx.ent, portName)
        except NoValueExc:  # pragma: no cover
            self.assertTrue(False, f"port {portName:s} exists")
        self.assertEqual(p.direction, direction, f"port {portName:s} should have direction {direction:s}")

    def assertDirIn(self, u: HwModule, portName: str):
        self.assertDir(u, portName, DIRECTION.IN)

    def assertDirOut(self, u: HwModule, portName: str):
        self.assertDir(u, portName, DIRECTION.OUT)

    @staticmethod
    def getPort(modDec: HdlModuleDec, portName: str):
        return single(modDec.ports, lambda x: x.name == portName)
