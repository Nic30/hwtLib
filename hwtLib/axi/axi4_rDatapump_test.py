import unittest

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.axi.axi4_rDatapump import Axi4_RDataPump


class Axi4_rDatapumpTC(unittest.TestCase):
    def setUp(self):
        u = Axi4_RDataPump()
        self.u, self.model, self.procs = simPrepare(u)
    
    def doSim(self, name, time):
        simUnitVcd(self.model, self.procs,
                    "tmp/axi4_rDatapump_" + name + ".vcd",
                    time=time)
    
    def test_nop(self):
        u = self.u
        self.doSim("nop", 200 * Time.ns)
        
        self.assertEqual(len(u.ar._ag.data), 0)
        self.assertEqual(len(u.rOut._ag.data), 0)
        
    def test_notSplitedReq(self):
        u = self.u
        
        req = u.req._ag
        
        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        self.doSim("notSplited", 200 * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.ar._ag.data), 1)
        self.assertEqual(len(u.rOut._ag.data), 0)
    
    def test_notSplitedReqWithData(self):
        u = self.u
        
        req = u.req._ag
        r = u.r._ag
        
        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        for i in range(3):
            r.addData(i + 77)
        
        self.doSim("notSplitedReqWithData", 200 * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.ar._ag.data), 1)
        self.assertEqual(len(u.rOut._ag.data), 1)
        self.assertEqual(valuesToInts(u.rOut._ag.data[0]), [77, mask(64 // 8), 0, 1])
        self.assertEqual(len(r.data), 2-1) # 2. is now sended
         
    
    def test_maxNotSplitedReqWithData(self):
        u = self.u
        
        req = u.req._ag
        r = u.r._ag
        
        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 255))
        for i in range(256):
            r.addData(i + 77, last=(i==255))
        
        self.doSim("maxNotSplitedReqWithData", 2600 * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.ar._ag.data), 1)
        self.assertEqual(len(u.rOut._ag.data), 256)
        # self.assertEqual(valuesToInts(u.rOut._ag.data[0]), [77, mask(64 // 8), 0, 1])
        self.assertEqual(len(r.data), 0) # 2. is now sended
       
        

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(Axi4_rDatapumpTC('test_maxNotSplitedReqWithData'))
    #suite.addTest(unittest.makeSuite(Axi4_rDatapumpTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    
    #import cProfile, pstats
    #cProfile.run("runner.run(suite)", "{}.profile".format(__file__))
    #s = pstats.Stats("{}.profile".format(__file__))
    #s.strip_dirs()
    #s.sort_stats("cumtime").print_stats(50)
    
