#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_comp.interconnect.base import AxiInterconnectBase
from hwtLib.amba.datapump.intf import AxiRDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo


@serializeParamsUniq
class RStrictOrderInterconnect(AxiInterconnectBase):
    """
    Strict order interconnect for AxiRDatapumpIntf (N-to-1)
    ensures that response on request is delivered to driver which asked for it
    while transactions can overlap

    .. hwt-autodoc::
    """

    def _config(self):
        self.DRIVER_CNT = Param(2)
        self.MAX_TRANS_OVERLAP = Param(16)
        AxiRDatapumpIntf._config(self)

    def getDpIntf(self, unit):
        return unit.rDatapump

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.drivers = HObjList(
                AxiRDatapumpIntf() for _ in range(int(self.DRIVER_CNT))
            )
            self.rDatapump = AxiRDatapumpIntf()._m()

        self.DRIVER_INDEX_WIDTH = log2ceil(self.DRIVER_CNT)

        f = self.orderInfoFifo = HandshakedFifo(Handshaked)
        f.DEPTH = self.MAX_TRANS_OVERLAP
        f.DATA_WIDTH = self.DRIVER_INDEX_WIDTH

    def _impl(self):
        assert int(self.DRIVER_CNT) > 1, "It makes no sense to use interconnect in this case"
        propagateClkRstn(self)
        self.reqHandler(self.rDatapump.req, self.orderInfoFifo.dataIn)

        fifoOut = self.orderInfoFifo.dataOut
        r = self.rDatapump.r

        driversR = [d.r for d in self.drivers]

        selectedDriverReady = self._sig("selectedDriverReady")
        selectedDriverReady(Or(*[fifoOut.data._eq(di) & d.ready
                                 for di, d in enumerate(driversR)
                                 ]))

        # extra enable signals based on selected driver from orderInfoFifo
        # extraHsEnableConds = {
        #                      r : fifoOut.vld  # on end of frame pop new item
        #                     }
        for i, d in enumerate(driversR):
            # extraHsEnableConds[d]
            d.valid(r.valid & fifoOut.vld & fifoOut.data._eq(i))
            d(r, exclude=[d.valid, d.ready])

        r.ready(fifoOut.vld & selectedDriverReady)
        fifoOut.rd(r.valid & r.last & selectedDriverReady)
        # StreamNode(masters=[r],
        #           slaves=driversR,
        #           extraConds=extraHsEnableConds).sync()


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = RStrictOrderInterconnect()
    print(to_rtl_str(u))
