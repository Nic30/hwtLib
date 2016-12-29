import unittest
from hwt.hdlObjects.constants import INTF_DIRECTION, DIRECTION
from hwt.pyUtils.arrayQuery import single, NoValueExc


class BaseSynthesizerTC(unittest.TestCase):
    def assertIsM(self, intf):
        self.assertEqual(intf._direction, INTF_DIRECTION.MASTER)
    
    def assertIsS(self, intf):
        self.assertEqual(intf._direction, INTF_DIRECTION.SLAVE)
        
    def assertDir(self, u, portName, direction):
        try:
            p = self.getPort(u._entity, portName)
        except NoValueExc:
            self.assertTrue(False, "port %s exists" % portName)
        self.assertEqual(p.direction, direction, "port %s should have direction %s" % (portName, direction))
    
    def assertDirIn(self, u, portName):
        self.assertDir(u, portName, DIRECTION.IN)
    
    def assertDirOut(self, u, portName):
        self.assertDir(u, portName, DIRECTION.OUT)
    
    @staticmethod
    def getPort(entity, portName):
        return single(entity.ports, lambda x: x.name == portName)
        