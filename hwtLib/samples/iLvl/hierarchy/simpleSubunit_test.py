#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import copy
import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.iLvl.hierarchy.simpleSubunit import SimpleSubunit


# SimTestCase is derived from unittest.TestCase which is class of unit test framework
# integrated in python itself
class SimpleSubunitTC(SimTestCase):

    # if method name starts with "test" unittest framework know that this method is test
    def test_simple(self):
        # create a unit instance
        u = SimpleSubunit()

        # convert it to rtl level
        # decorate interface with agents (._ag property) which will drive or monitor values on the interface
        self.prepareUnit(u)

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
        # we save dum of value changes into file "tmp/simple.vcd" (which is default)
        # and we let simulation run for 100 ns
        self.doSim(100*Time.ns)

        # now we use part of unittest framework to check results
        # use assertValSequenceEqual which sill automatically convert
        # value objects to integer representation and checks them
        self.assertValSequenceEqual(u.b._ag.data, expected)

        # you can also access signals inside model by it's signal names
        # this names can differ in order to avoid name collision (suffix is usually used, or invalid character is replaced)
        self.assertValEqual(self.model.subunit0_inst.a._val, 0)

if __name__ == "__main__":
    # this is how you can run testcase,
    # there are many way and lots of tools support direct running of tests (like eclipse)
    suite = unittest.TestSuite()

    # this is how you can select specific test
    # suite.addTest(SimpleSubunitTC('test_simple'))

    # this is how you add all test from testcase
    suite.addTest(unittest.makeSuite(SimpleSubunitTC))

    runner = unittest.TextTestRunner(verbosity=3)

    runner.run(suite)
