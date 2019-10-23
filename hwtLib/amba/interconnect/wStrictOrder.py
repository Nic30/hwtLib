#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, connect, Or, Switch
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_comp.axi_datapump_intf import AxiWDatapumpIntf
from hwtLib.amba.interconnect.axiInterconnectbase import AxiInterconnectBase
from hwtLib.handshaked.fifo import HandshakedFifo


@serializeParamsUniq
class WStrictOrderInterconnect(AxiInterconnectBase):
    """
    Strict order interconnect for AxiWDatapumpIntf
    ensures that response on request is delivered to driver which asked for it while transactions can overlap
    
    .. hwt-schematic::
    """

    def _config(self):
        self.DRIVER_CNT = Param(2)
        self.MAX_TRANS_OVERLAP = Param(16)
        AxiWDatapumpIntf._config(self)

    def getDpIntf(self, unit):
        return unit.wDatapump

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.drivers = HObjList(
                AxiWDatapumpIntf()
                for _ in range(int(self.DRIVER_CNT)))
            self.wDatapump = AxiWDatapumpIntf()._m()

        self.DRIVER_INDEX_WIDTH = log2ceil(self.DRIVER_CNT)

        fW = self.orderInfoFifoW = HandshakedFifo(Handshaked)
        fAck = self.orderInfoFifoAck = HandshakedFifo(Handshaked)
        for f in [fW, fAck]:
            f.DEPTH = self.MAX_TRANS_OVERLAP
            f.DATA_WIDTH = self.DRIVER_INDEX_WIDTH

    def wHandler(self):
        w = self.wDatapump.w
        fWOut = self.orderInfoFifoW.dataOut
        fAckIn = self.orderInfoFifoAck.dataIn

        driversW = list(map(lambda d: d.w,
                            self.drivers))

        selectedDriverVld = self._sig("selectedDriverWVld")
        selectedDriverVld(Or(*map(lambda d: fWOut.data._eq(d[0]) & d[1].valid,
                                  enumerate(driversW))
                            ))
        selectedDriverLast = self._sig("selectedDriverLast")
        selectedDriverLast(Or(*map(lambda d: fWOut.data._eq(d[0]) & d[1].last,
                                   enumerate(driversW))
                             ))

        Switch(fWOut.data).addCases(
            [(i, connect(d, w, exclude=[d.valid, d.ready]))
               for i, d in enumerate(driversW)]

        ).Default(
            w.data(None),
            w.strb(None),
            w.last(None)
        )

        fAckIn.data(fWOut.data)

        # handshake logic
        fWOut.rd(selectedDriverVld & selectedDriverLast & w.ready & fAckIn.rd)
        for i, d in enumerate(driversW):
            d.ready(fWOut.data._eq(i) & w.ready & fWOut.vld & fAckIn.rd)
        w.valid(selectedDriverVld & fWOut.vld & fAckIn.rd)
        fAckIn.vld(selectedDriverVld & selectedDriverLast & w.ready & fWOut.vld)

        #extraConds = {
        #    fAckIn: selectedDriverLast
        #    }
        #for i, d in enumerate(driversW):
        #    extraConds[d] = fWOut.data._eq(i)
        #    
        #StreamNode(masters=[w, fWOut], 
        #           slaves=driversW+[fAckIn],
        #           extraConds=extraConds).sync()

    def ackHandler(self):
        ack = self.wDatapump.ack
        fAckOut = self.orderInfoFifoAck.dataOut
        driversAck = list(map(lambda d: d.ack,
                              self.drivers))

        selectedDriverAckReady = self._sig("selectedDriverAckReady")
        selectedDriverAckReady(Or(*map(lambda d: fAckOut.data._eq(d[0]) & d[1].rd,
                                       enumerate(driversAck))
                                 ))

        ack.rd(fAckOut.vld & selectedDriverAckReady)
        fAckOut.rd(ack.vld & selectedDriverAckReady)

        for i, d in enumerate(driversAck):
            connect(ack, d, exclude=[d.vld, d.rd])
            d.vld(ack.vld & fAckOut.vld & fAckOut.data._eq(i))

    def _impl(self):
        assert int(self.DRIVER_CNT) > 1, "It makes no sense to use interconnect in this case"
        propagateClkRstn(self)
        self.reqHandler(self.wDatapump.req, self.orderInfoFifoW.dataIn)
        self.wHandler()
        self.ackHandler()


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = WStrictOrderInterconnect()
    print(toRtl(u))
