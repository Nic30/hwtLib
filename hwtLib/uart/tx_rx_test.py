from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked, VldSynced
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.agentConnector import valToInt
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.uart.rx import UartRx
from hwtLib.uart.tx import UartTx


class TestUnit_uart(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.FREQ = Param(115200*16)
        self.BAUD = Param(115200)
        self.OVERSAMPLING = Param(16)
    
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.din = Handshaked()
            self.dout = VldSynced()

            self.tx = UartTx()
            self.rx = UartRx()

    def _impl(self):
        propagateClkRstn(self)
        self.rx.rxd ** self.tx.txd
        self.tx.dataIn ** self.din
        self.dout ** self.rx.dataOut
        
        
class UartTxRxTC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u = TestUnit_uart()
        u.BAUD.set(115200)
        u.FREQ.set(115200*16)
        u.OVERSAMPLING.set(16)
        self.prepareUnit(u)
    
    def getStr(self):
        return "".join([chr(valToInt(d)) for d in self.u.dout._ag.data])
    
    def sendStr(self, string):
        for s in string:
            self.u.din._ag.data.append(ord(s))
    
    def test_nop(self):
        self.doSim(200 * Time.ns)
        self.assertEqual(self.getStr(), "")
        
        
    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.doSim(10 * 10 * (len(t) * 16 + 10) * Time.ns)
        self.assertEqual(self.getStr(), t)
        
        

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(UartTxTC('test_multiple_randomized2'))
    suite.addTest(unittest.makeSuite(UartTxRxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
