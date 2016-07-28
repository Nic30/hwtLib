from copy import copy
import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd 
from hdl_toolkit.synthetisator.shortcuts import synthesised
from hwtLib.samples.iLvl.hierarchy.simpleSubunit import SimpleSubunit


# unittest.TestCase is class of unit test framework integrated in python
class SimpleTC(unittest.TestCase):
   
    # if method name starts with "test" unittest framework know that this method is test 
    def testSimple(self):
        # create a unit instance
        u = SimpleSubunit()
        # convert it to rtl level
        synthesised(u)
        
        # decorate interface with agents (._ag property) which will drive or monitor values on the interface
        # there drivers and monitors are returned and stored in procs, we will need them for simulation
        procs = autoAddAgents(u)
        
        # there we have our test data, because SimpleSubunit has only connection inside 
        # None represents invalid value (like universal "x" in vhdl)
        inputData = [0, 1, 0, 1, None, 0, None, 1, None, 0]
        
        # expected data are same as input data, 
        # but because data in inputData will be consumed, we have to make a copy 
        expected = copy(inputData)
        
        # assign inputData to data property of agent for interface "a"
        # now in simulation driver of a will pop data from input data and it will put them on interface "a"
        u.a._ag.data = inputData
        
        # now we run simulation, we use our unit "u", our monitors and drivers of interfaces stored in "procs",
        # we save dum of value changes into file "tmp/simple.vcd"
        # and we let simulation run for 100 ns
        simUnitVcd(u, procs, "tmp/simple.vcd", time=100 * HdlSimulator.ns)
        
        # now we use part of unittest framework to check results
        self.assertSequenceEqual(expected, agInts(u.b))
    
if __name__ == "__main__":
    # this is how you can run testcase, 
    # there are many way and lots of tools support direct running of tests (like eclipse)
    suite = unittest.TestSuite()
    
    # this is how you can select specific test
    # suite.addTest(TwoCntrsTC('test_withStops'))
    
    #this is how you add all test from testcase
    suite.addTest(unittest.makeSuite(SimpleTC))

    runner = unittest.TextTestRunner(verbosity=3)
    
    runner.run(suite)
