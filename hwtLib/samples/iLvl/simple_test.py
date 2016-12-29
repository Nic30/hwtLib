#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import copy
import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.simple import SimpleUnit


# unittest.TestCase is class of unit test framework integrated in python
class SimpleTC(unittest.TestCase):
   
    # if method name starts with "test" unittest framework know that this method is test 
    def test_simple(self):
        # create a unit instance
        u = SimpleUnit()
        # convert it to rtl level
        # decorate interface with agents (._ag property) which will drive or monitor values on the interface
        # there drivers and monitors are returned and stored in procs, we will need them for simulation
        u, model, procs = simPrepare(u)
        
        
        # there we have our test data, because SimpleUnit has only connection inside 
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
        simUnitVcd(model, procs, "tmp/simple.vcd", time=100 * Time.ns)
        
        # now we use part of unittest framework to check results
        # we use agInts to convert value objects to integer representation
        self.assertSequenceEqual(expected, agInts(u.b))
    
if __name__ == "__main__":
    # this is how you can run testcase, 
    # there are many way and lots of tools support direct running of tests (like eclipse)
    suite = unittest.TestSuite()
    
    # this is how you can select specific test
    # suite.addTest(SimpleTC('test_simple'))
    
    # this is how you add all test from testcase
    suite.addTest(unittest.makeSuite(SimpleTC))

    runner = unittest.TextTestRunner(verbosity=3)
    
    runner.run(suite)
