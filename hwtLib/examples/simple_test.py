#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.simple import SimpleUnit


# SimTestCase is derived from unittest.TestCase
# which is class of unit test framework integrated in python itself
class SimpleTC(SimTestCase):

    # if method name starts with "test" unittest framework
    # know that this method is test
    def test_simple(self):
        # create a unit instance
        u = SimpleUnit()
        # convert it to rtl level
        # decorate interface with agents (._ag property) which will
        # drive or monitor values on the interface
        self.compileSimAndStart(u)

        # there we have our test data, because SimpleUnit has only connection inside
        # None represents invalid value (like universal "x" in vhdl)
        inputData = [0, 1, 0, 1, None, 0, None, 1, None, 0]

        # add inputData to agent for interface "a"
        # now agent of "a" will popleft data from input data
        # and it will put them on interface "a"
        u.a._ag.data.extend(inputData)

        # now we run simulation, we use our unit "u", our monitors
        # and drivers of interfaces stored in "procs",
        # we save dum of value changes into file "tmp/simple.vcd"
        # (which is default) and we let simulation run for 100 ns
        self.runSim(100*Time.ns)

        # now we use part of unittest framework to check results
        # use assertValSequenceEqual which sill automatically convert
        # value objects to integer representation and checks them
        self.assertValSequenceEqual(u.b._ag.data, inputData)


if __name__ == "__main__":
    # this is how you can run testcase
    suite = unittest.TestSuite()

    # this is how you can select specific test
    # suite.addTest(SimpleTC('test_simple'))

    # this is how you add all test from testcase
    suite.addTest(unittest.makeSuite(SimpleTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
