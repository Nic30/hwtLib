# hwtLib

[![Travis-ci Build Status](https://travis-ci.org/Nic30/hwtLib.png?branch=master)](https://travis-ci.org/Nic30/hwtLib)[![PyPI version](https://badge.fury.io/py/hwtLib.svg)](http://badge.fury.io/py/hwtLib)[![Coverage Status](https://coveralls.io/repos/github/Nic30/hwtLib/badge.svg?branch=master)](https://coveralls.io/github/Nic30/hwtLib?branch=master)[![Documentation Status](https://readthedocs.org/projects/hwtlib/badge/?version=latest)](http://hwtlib.readthedocs.io/en/latest/?badge=latest)
 
Library can be installed by command: 
``` bash
sudo pip3 install hwtLib
```

hwtLib is the library of hardware components for [hwt framework](https://github.com/Nic30/hwt). Relation of hwt and hwtLib is similar as C and stdlib relation. 


Any component can be exported as IPCore using Packager class from hwt or as HDL code by toRtl(). Target language is specified by keyword serializer.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.handshaked.builder import HsBuilder

class HandshakedBuilderSimple(Unit):
    """
    Simple example of HsBuilder which can build components
    for Handshaked interfaces
    """
    def _declr(self):
        # declare interfaces
        addClkRstn(self)
        self.a = Handshaked()
        self.b = Handshaked()

    def _impl(self):
        # instanciate builder
        b = HsBuilder(self, self.a)

        # HsBuilder is derived from AbstractStreamBuilder and implements
        # it can:
        # * instantiate and connect:
        #    * fifos, registers, delays
        #    * frame builders, frame parsers
        #    * data width resizers
        #    * various stream join/split components
        #    * clock domain crossing
        # there are other examples in https://github.com/Nic30/hwtLib/tree/master/hwtLib/samples/builders

        # for most of stream interfaces like AvalonST, FrameLink ...
        # there is builder with same program interface

        # instanciate handshaked register (default buff items=1)
        # and connect it to end (which is self.a)
        b.buff()

        # instantiate fifo with 16 items and connect it to output of register
        # from previous step
        b.buff(items=16)

        # instantiate register with latency=2 and delay=1 and connect it
        # to output of fifo from previous step
        b.buff(latency=2, delay=1)

        # b.end is now output of register from previous step,
        # connect it to uptput
        self.b(b.end)


# SimTestCase is unittest.TestCase with some extra methods
class HandshakedBuilderSimpleTC(SimTestCase):
    def test_passData(self):
        u = HandshakedBuilderSimple()
        # instanciate simulation agents and convert unit to simulation model
        self.prepareUnit(u)

        # add data on input of agent for "a" interface
        u.a._ag.data.extend([1, 2, 3, 4])

        self.runSim(200 * Time.ns)

        # check if data was recieved on "b" interface 
        self.assertValSequenceEqual(u.b._ag.data, [1, 2, 3, 4])




if __name__ == "__main__":
    import unittest
    from hwt.synthesizer.utils import toRtl
    from hwt.serializer.ip_packager.packager import Packager

    # run tests (standard unittest framework from python)
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HandshakedBuilderSimpleTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    
    # instanciate component
    u = HandshakedBuilderSimple()

    # export component as IPCore
    p = Packager(u)
    p.createPackage(".")
```



Repositories with opensource HW:

https://github.com/enjoy-digital?tab=repositories

https://github.com/cfelton/rhea

https://github.com/FPGAwars/FPGA-peripherals
