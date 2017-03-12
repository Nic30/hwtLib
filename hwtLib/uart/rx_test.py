from hwt.simulator.simTestCase import SimTestCase
from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import valToInt
from hwtLib.uart.rx import UartRx
from hwt.bitmask import selectBit


class UartRxTC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        self.OVERSAMPLING = 16

        u = self.u = UartRx()
        u.BAUD.set(115200)
        u.FREQ.set(115200 * self.OVERSAMPLING)
        u.OVERSAMPLING.set(self.OVERSAMPLING)
        
        self.prepareUnit(u)
    
    def getStr(self):
        s = ""
        for d in self.u.dataOut._ag.data:
            ch = valToInt(d)
            s += chr(ch)
            
        return s
    
    def sendStr(self, string):
        START_BIT = 0
        STOP_BIT = 1
        
        rx = self.u.rxd._ag.data
        os = self.OVERSAMPLING
        for ch in string:
            rx.extend([START_BIT for _ in range(os)])
            for i in range(8):
                d = selectBit(ord(ch), i)
                rx.extend([d for _ in range(os)])
            rx.extend([STOP_BIT for _ in range(os)])        
    
    def test_nop(self):
        self.doSim(200 * Time.ns, )
        self.assertEqual(self.getStr(), "")
        
        
    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.doSim(self.OVERSAMPLING * 10 * 10 * (len(t) + 5) * Time.ns)
        self.assertEqual(self.getStr(), t)
        
        

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(UartRxTC('test_simple'))
    suite.addTest(unittest.makeSuite(UartRxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
