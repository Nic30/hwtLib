#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.simpleHwModule import SimpleHwModule


# SimTestCase is derived from unittest.TestCase
# which is class of unit test framework integrated in python itself
class SimpleTC(SimTestCase):

    def tearDown(self):
        # common cleanup, not necessary but should be used when compileSimAndStart is used explicitly
        # because otherwise the old simulation is restarted for a next test
        self.rmSim()
        SimTestCase.tearDown(self)

    # if method name starts with "test" unittest framework
    # know that this method is test
    def test_simple(self):
        # create a unit instance
        dut = SimpleHwModule()
        # convert it to rtl level
        # decorate interface with agents (._ag property) which will
        # drive or monitor values on the interface
        self.compileSimAndStart(dut)

        # there we have our test data, because SimpleHwModule has only connection inside
        # None represents invalid value (like universal "x" in vhdl)
        inputData = [0, 1, 0, 1, None, 0, None, 1, None, 0]

        # add inputData to agent for interface "a"
        # now agent of "a" will popleft data from input data
        # and it will put them on interface "a"
        dut.a._ag.data.extend(inputData)

        # now we run simulation, we use our unit "dut", our monitors
        # and drivers of interfaces stored in "procs",
        # we save dum of value changes into file "tmp/simple.vcd"
        # (which is default) and we let simulation run for 100 ns
        self.runSim(100 * Time.ns)

        # now we use part of unittest framework to check results
        # use assertValSequenceEqual which sill automatically convert
        # value objects to integer representation and checks them
        self.assertValSequenceEqual(dut.b._ag.data, inputData)


if __name__ == "__main__":
    # This is one of ways how to run tests in python unittest framework (nothing HWT specific)
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(SimpleTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
