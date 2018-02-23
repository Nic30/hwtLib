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
    from hwt.synthesizer.utils import toRtl
    print(toRtl(HandshakedBuilderSimple()))
