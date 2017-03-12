from hwt.simulator.simTestCase import SimTestCase
from hwtLib.uart.tx import UartTx
from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import valToInt


class UartTxTC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u = UartTx()
        u.BAUD.set(115200)
        u.FREQ.set(115200)
        self.prepareUnit(u)
        self.randomize(u.dataIn)
    
    def getStr(self):
        START_BIT = 0
        STOP_BIT = 1 
        s = ""
        d = iter(self.u.txd._ag.data)
        for bit in d:
            self.assertEqual(bit.vldMask, 0b1)
            _bit = valToInt(bit)
            
            if _bit == START_BIT:
                ch = 0
                for i in range(10 - 1):
                    b = next(d)
                    self.assertEqual(b.vldMask, 0b1)
                    _b = valToInt(b)
                    if i == 8:
                        self.assertEqual(_b, STOP_BIT) 
                    else:
                        ch |= _b << i
                        
                s = s + chr(ch)
        
        return s
    
    def sendStr(self, string):
        for ch in string:
            self.u.dataIn._ag.data.append(ord(ch))
        
    
    def test_nop(self):
        self.doSim(200 * Time.ns)
        self.assertEqual(self.getStr(), "")
        
        
    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.doSim(10 * 10 * (len(t) + 10) * Time.ns)
        self.assertEqual(self.getStr(), t)
        
        

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(UartTxTC('test_multiple_randomized2'))
    suite.addTest(unittest.makeSuite(UartTxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
