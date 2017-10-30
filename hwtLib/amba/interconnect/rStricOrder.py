#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, connect, Or
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwtLib.amba.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.amba.interconnect.axiInterconnectbase import AxiInterconnectBase
from hwtLib.handshaked.fifo import HandshakedFifo


@serializeParamsUniq
class RStrictOrderInterconnect(AxiInterconnectBase):
    """
    Strict order interconnect for AxiRDatapumpIntf
    ensures that response on request is delivered to driver which asked for it while transactions can overlap
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
            self.drivers = AxiRDatapumpIntf(asArraySize=self.DRIVER_CNT)
            self.rDatapump = AxiRDatapumpIntf()

        self.DRIVER_INDEX_WIDTH = log2ceil(self.DRIVER_CNT).val

        f = self.orderInfoFifo = HandshakedFifo(Handshaked)
        f.DEPTH.set(self.MAX_TRANS_OVERLAP)
        f.DATA_WIDTH.set(self.DRIVER_INDEX_WIDTH)

    def _impl(self):
        assert int(self.DRIVER_CNT) > 1, "It makes no sense to use interconnect in this case"
        propagateClkRstn(self)
        self.reqHandler(self.rDatapump.req, self.orderInfoFifo.dataIn)

        fifoOut = self.orderInfoFifo.dataOut
        r = self.rDatapump.r

        driversR = list(map(lambda d: d.r,
                            self.drivers))

        selectedDriverReady = self._sig("selectedDriverReady")
        selectedDriverReady(Or(*map(lambda d: fifoOut.data._eq(d[0]) & d[1].ready,
                                    enumerate(driversR))
                                    ))

        # extra enable signals based on selected driver from orderInfoFifo
        # extraHsEnableConds = {
        #                      r : fifoOut.vld  # on end of frame pop new item
        #                     }
        for i, d in enumerate(driversR):
            # extraHsEnableConds[d]
            d.valid(r.valid & fifoOut.vld & fifoOut.data._eq(i))
            connect(r, d, exclude=[d.valid, d.ready])

        r.ready(fifoOut.vld & selectedDriverReady)
        fifoOut.rd(r.valid & r.last & selectedDriverReady)
        # StreamNode(masters=[r],
        #           slaves=driversR,
        #           extraConds=extraHsEnableConds).sync()


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = RStrictOrderInterconnect()
    print(toRtl(u))
