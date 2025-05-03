#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.builder import HsBuilder


class HandshakedBuilderSimple(HwModule):
    """
    Simple example of HsBuilder which can build components
    for HwIODataRdVld interfaces

    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        # declare interfaces
        addClkRstn(self)
        self.a = HwIODataRdVld()
        self.b = HwIODataRdVld()._m()

    @override
    def hwImpl(self):
        # instantiate builder
        b = HsBuilder(self, self.a)

        # HsBuilder is derived from AbstractStreamBuilder and implements
        # it can:
        # * instantiate and connect:
        #    * FIFOs, registers, delays
        #    * frame builders, frame parsers
        #    * data width resizers
        #    * various stream join/split components
        #    * clock domain crossing

        # for most of stream interfaces like AvalonST, LocalLink ...
        # there is builder with same program interface

        # instantiate handshaked register (default buff items=1)
        # and connect it to end (which is self.a)
        b.buff()

        # instantiate fifo with 16 items and connect it to output of register
        # from previous step
        b.buff(items=16)

        # instantiate register with latency=2 and delay=1 and connect it
        # to output of FIFO from previous step
        b.buff(latency=2, delay=1)

        # b.end is now output of register from previous step,
        # connect it to input
        self.b(b.end)


# SimTestCase is unittest.TestCase with some extra methods
class HandshakedBuilderSimpleTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        # SimTestCase.setUpClass calls this method
        # and will build a simulator of this component
        cls.dut = HandshakedBuilderSimple()
        cls.compileSim(cls.dut)

    def test_passData(self):
        # now in setUpClass call the simulator was build
        #     in setU       call the simulator was initialized
        #                   and signals in .dut are replaced
        #                   with proxies for simulator
        dut = self.dut
        # add data on input of agent for "a" interface
        dut.a._ag.data.extend([1, 2, 3, 4])

        self.runSim(200 * Time.ns)

        # check if data was received on "b" interface
        self.assertValSequenceEqual(dut.b._ag.data, [1, 2, 3, 4])


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(HandshakedBuilderSimple()))
