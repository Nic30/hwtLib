#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.handshaked.builder import HsBuilder


class HsBuilderSplit(Unit):
    """
    Example of HsBuilder.split_* functions

    .. hwt-schematic::
    """
    def _declr(self):
        addClkRstn(self)

        self.a = Handshaked()
        self.a_0 = Handshaked()._m()
        self.a_1 = Handshaked()._m()
        self.a_2 = Handshaked()._m()

        self.b = Handshaked()
        self.b_0 = Handshaked()._m()
        self.b_1 = Handshaked()._m()
        self.b_2 = Handshaked()._m()
        self.b_selected = Handshaked()._m()
        self.b_selected.DATA_WIDTH = 3

        self.c = Handshaked()
        self.c_0 = Handshaked()._m()
        self.c_1 = Handshaked()._m()

        self.d = Handshaked()
        self.d_0 = Handshaked()._m()
        self.d_1 = Handshaked()._m()
        self.d_2 = Handshaked()._m()

        self.e = Handshaked()
        self.e_0 = Handshaked()._m()
        self.e_1 = Handshaked()._m()
        self.e_2 = Handshaked()._m()
        self.e_select = Handshaked()
        self.e_select.DATA_WIDTH = 3

    def _impl(self):
        # Builder is class which simplifies building of datapaths
        # and keeps components which are used  which this interface together
        a = HsBuilder(self, self.a, name="builderFromA")
        # .end = last interface in datapath
        # .lastComp = last component in datapath
        # ... take a look at AbstractStreamBuilder

        # register
        a.buff(items=1, latency=1, delay=0)

        # fifo
        a.buff(items=4, latency=1, delay=0)

        # reg + fifo
        a.buff(items=5, latency=2, delay=0)

        # reg wit delay (breaks combinational loop of ready signal)
        a.buff(items=1, latency=2, delay=1)

        # create 3 identhical streams and connect them to a_0-3
        # there is also only split_copy which only create split component
        # but left output unconnected
        a.split_copy_to(self.a_0, self.a_1, self.a_2)

        # round robin like split, data is send only to one of output ports
        # and there is cycling flag which selects priority for each output
        # to assert uniform load
        b = HsBuilder(self, self.b)\
            .split_fair_to(self.b_0, self.b_1, self.b_2,
                           exportSelected=True)

        self.b_selected(b.lastComp.selectedOneHot)

        # send data output interface which is ready and has higher priority
        # (=lowest index)
        HsBuilder(self, self.c).split_prioritized_to(self.c_0, self.c_1)

        # explicitly select output
        HsBuilder(self, self.d)\
            .split_select_to([1, 2, 1, 0],
                             self.d_0, self.d_1, self.d_2)

        # explicitly select output
        HsBuilder(self, self.e)\
            .split_select_to(self.e_select,
                             self.e_0, self.e_1, self.e_2)


if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it only when this script is running as main
    from hwt.synthesizer.utils import toRtl
    # we create instance of our unit
    u = HsBuilderSplit()
    # there is more of synthesis methods. toRtl() returns formated hdl string
    print(toRtl(u))
