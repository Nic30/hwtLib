#!/usr/bin/env python3arent
# -*- coding: utf-8 -*-

from typing import Dict, Optional

from hwt.hwIOs.std import HwIOClk, HwIORst_n, HwIODataRdVld
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwtLib.abstract.debug_bus_monitor import DebugBusMonitor, \
    DebugBusMonitorDataRecord
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.handshaked.reg import HandshakedReg


class DebugBusMonitorExampleAxi(HwModule):
    """
    An example how to use :class:`hwtLib.abstract.debug_bus_monitor.DebugBusMonitor`

    .. hwt-autodoc::
    """

    def _config(self):
        Axi4Lite._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.s = Axi4Lite()
        self.din0 = HwIODataRdVld()
        self.dout0 = HwIODataRdVld()._m()
        self.reg = HandshakedReg(HwIODataRdVld)
        self.din1 = HwIODataRdVld()
        self.dout1 = HwIODataRdVld()._m()

        self.other_clk = HwIOClk()
        self.other_clk.FREQ = self.clk.FREQ * 2
        with self._associated(clk=self.other_clk):
            self.other_rst_n = HwIORst_n()
            self.din2 = HwIODataRdVld()
            self.dout2 = HwIODataRdVld()._m()

    def _impl(self):

        # spy on previously generated circuit
        db = DebugBusMonitor(Axi4Lite, AxiLiteEndpoint)
        intf_to_dbg: Dict[HwIODataRdVld, DebugBusMonitorDataRecord] = {}

        def spy_connections(i: HwIODataRdVld):
            """
            * Construct a record in DebugBusMonitor for a specified interface.
            * Link to other visual nodes on connections.
            * Automatically build nodes for visual hierarchy.
            """
            # cdc if the interface ussing a different clock signal
            parent = i._parent
            parents = []
            while parent is not self:
                parents.append(parent)
                parent = parent._parent

            parent_node: Optional[DebugBusMonitorDataRecord] = None
            for o in reversed(parents):
                n = intf_to_dbg.get(o, None)
                if n is None:
                    n = intf_to_dbg[o] = DebugBusMonitorDataRecord(None, o._name, False, False, False)
                    db.monitored_data.append(n)

                if parent_node is not None:
                    parent_node.children.append(n)
                parent_node = n

            cdc = i._getAssociatedClk() is not self.clk
            n0 = db.register(i, cdc=cdc)
            intf_to_dbg[i] = n0
            n1 = db.register(i, name=i._name + "_snapshot",
                        cdc=cdc,
                        trigger=i.vld & i.rd)

            n0.add_link(n1)
            if parent_node is not None:
                parent_node.add_children(n0)
                parent_node.add_children(n1)

            orig_connect = i._connectTo

            def  _connectTo(master, exclude=None, fit=False):
                n0 = intf_to_dbg[master]
                n1 = intf_to_dbg[i]
                n0.add_link(n1)
                return orig_connect(master, exclude=exclude, fit=fit)

            i._connectTo = _connectTo

        for i in [self.din0,
                  self.dout0, self.din1,
                  self.reg.dataIn, self.reg.dataOut,
                  self.dout1,
                  self.din2,
                  self.dout2,
                  ]:
            spy_connections(i)

        # some connections
        self.dout0(self.din0)
        self.reg.dataIn(self.din1)
        self.dout1(self.reg.dataOut)
        self.dout2(self.din2)
        intf_to_dbg[self.reg.dataIn].add_link(intf_to_dbg[self.reg.dataOut])

        # we need to add register for ".s" because otherwise there would be
        # a combinational loop
        # db.register(self.s, add_reg=True)
        # for hwIO in self.s._hwIOs:
        #    db.register(hwIO, name="s_" + hwIO._name + "_snapshot",
        #                trigger=hwIO.valid & hwIO.ready)

        with self._hwParamsShared():
            self.db = db
        db.s(self.s)
        # there we actually connect the monitored interface
        # to the monitor instance
        db.apply_connections()

        propagateClkRstn(self)


if __name__ == '__main__':
    from hwt.synth import to_rtl_str
    
    m = DebugBusMonitorExampleAxi()
    print(to_rtl_str(m))
