#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi3 import Axi3_withAddrUser


class AxiTestJunction(Unit):
    def __init__(self, axiCls):
        Unit.__init__(self)
        self.axiCls = axiCls

    def _declr(self):
        addClkRstn(self)
        self.s = self.axiCls()
        self.m = self.axiCls()
    
    def _impl(self):
        self.m ** self.s  


class Axi_ag_TC(SimTestCase):
    """
    Simple test of axi3/4 interfaces and agents for them
    """
    def randA(self):
        """get random address transaction"""
        r = self._rand.getrandbits
        _id = r(6)
        addr = r(32)
        burst = r(2)
        cache = r(4)
        _len = r(8)
        lock = r(1)
        prot = r(3)
        size = r(3)
        qos = r(4)
        
        return (_id, addr, burst, cache, _len, lock, prot, size, qos)
    
    def randA3u(self):
        """get random address transaction for axi 3 with user"""
        r = self._rand.getrandbits
        _id = r(6)
        addr = r(32)
        burst = r(2)
        cache = r(4)
        _len = r(4)
        lock = r(1)
        prot = r(3)
        size = r(3)
        qos = r(4)
        user = r(5)
        
        return (_id, addr, burst, cache, _len, lock, prot, size, qos, user)

    def randW(self):
        """get random data write transaction"""
        r = self._rand.getrandbits
        _id = r(6)
        data = r(64)
        strb = r(64 // 8)
        last = r(1)

        return (_id, data, strb, last)

    def randB(self):
        """get random data write acknowledge transaction"""
        r = self._rand.getrandbits
        _id = r(6)
        resp = r(2)
        return (_id, resp)
    
    def randR(self):
        """get random data read transaction"""
        r = self._rand.getrandbits
        _id = r(6)
        data = r(64)
        resp = r(2)
        last = r(1)
        return (_id, data, resp, last)
        
    def test_axi4_ag(self):
        """Test if axi4 agent can transmit and receive data on all channels"""
        u = AxiTestJunction(Axi4)
        self.prepareUnit(u)
        N = 10

        aw = [self.randA() for _ in range(N)]
        ar = [self.randA() for _ in range(N)]
        w = [self.randW() for _ in range(N)]
        b = [self.randB() for _ in range(N)]
        r = [self.randR() for _ in range(N)]
        
        u.s.aw._ag.data.extend(aw)
        u.s.ar._ag.data.extend(ar)
        
        u.s.w._ag.data.extend(w)
        
        u.m.r._ag.data.extend(r)
        u.m.b._ag.data.extend(b)
        
        self.doSim(20 * N * Time.ns)
        
        a = self.assertValSequenceEqual
        
        a(u.m.aw._ag.data, aw)
        a(u.m.ar._ag.data, ar)
        a(u.m.w._ag.data, w)
        
        a(u.s.r._ag.data, r)
        a(u.s.b._ag.data, b)
        
    
    def test_axi3_withAddrUser_ag(self):
        """Test if axi4 agent can transmit and receive data on all channels"""
        u = AxiTestJunction(Axi3_withAddrUser)
        self.prepareUnit(u)
        N = 10

        aw = [self.randA3u() for _ in range(N)]
        ar = [self.randA3u() for _ in range(N)]
        w = [self.randW() for _ in range(N)]
        b = [self.randB() for _ in range(N)]
        r = [self.randR() for _ in range(N)]
        
        u.s.aw._ag.data.extend(aw)
        u.s.ar._ag.data.extend(ar)
        
        u.s.w._ag.data.extend(w)
        
        u.m.r._ag.data.extend(r)
        u.m.b._ag.data.extend(b)
        
        self.doSim(20 * N * Time.ns)
        
        a = self.assertValSequenceEqual
        
        a(u.m.aw._ag.data, aw)
        a(u.m.ar._ag.data, ar)
        a(u.m.w._ag.data, w)
        
        a(u.s.r._ag.data, r)
        a(u.s.b._ag.data, b)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiTC('test_axi_size'))
    suite.addTest(unittest.makeSuite(Axi_ag_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)