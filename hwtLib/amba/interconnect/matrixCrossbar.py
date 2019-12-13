#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, Or, connect, Switch, Concat
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.interconnect.common import apply_name
from hwtLib.handshaked.streamNode import StreamNode


class AxiInterconnectMatrixCrossbar(Unit):
    """
    Crossbar for AXI-Stream like interfaces where internall switch box
    can be driven by 

    .. hwt-schematic:: example_AxiInterconnectMatrixCrossbar
    """

    def __init__(self, intfCls):
        self.intfCls = intfCls
        super(AxiInterconnectMatrixCrossbar, self).__init__()

    def _config(self):
        self.INPUT_CNT = Param(1)
        # set of input indexes for each output
        self.OUTPUTS = Param([{0}])
        self.intfCls._config(self)

    def _declr(self):
        # flag that tells if each master should track the order of request so it
        # can collect the data in same order
        self.REQUIRED_ORDER_SYNC_DIN_FOR_DOUT = self.INPUT_CNT > 1
        # flag which tells if each slave should track the origin of the request
        # so it later knows where to send the data
        self.REQUIRED_ORDER_SYNC_DOUT_FOR_DIN = len(self.OUTPUTS) > 1

        addClkRstn(self)
        AXI = self.intfCls
        INPUT_CNT = self.INPUT_CNT
        OUTPUT_CNT = len(self.OUTPUTS)
        with self._paramsShared():
            self.dataIn = HObjList([
                AXI()
                for _ in range(INPUT_CNT)])

        with self._paramsShared():
            self.dataOut = HObjList([
                AXI()._m()
                for _ in range(OUTPUT_CNT)])

        if self.REQUIRED_ORDER_SYNC_DOUT_FOR_DIN:
            # master index for each slave so slave knows
            # which master did read and where is should send it
            self.order_dout_index_for_din_in = HObjList([
                Handshaked() for _ in range(INPUT_CNT)])

            for f in self.order_dout_index_for_din_in:
                f.DATA_WIDTH = log2ceil(OUTPUT_CNT)

        if self.REQUIRED_ORDER_SYNC_DIN_FOR_DOUT:
            # slave index for each master
            # so master knows where it should expect the data
            self.order_din_index_for_dout_in = HObjList([
                Handshaked() for _ in range(OUTPUT_CNT)])

            for f in self.order_din_index_for_dout_in:
                f.DATA_WIDTH = log2ceil(INPUT_CNT)

    def get_last(self, intf):
        return intf.last

    def r_handler_N_to_M(self,
                         dataOut_channels,
                         dataIn_channels,
                         order_dout_index_for_din,
                         order_din_index_for_dout):

        for din_i, (order_m_for_s, dataIn) in enumerate(zip(order_dout_index_for_din, dataIn_channels)):
            selected_dataOut_ready = Or(*[
                order_m_for_s.data._eq(di)
                & order_s_for_m.data._eq(din_i)
                & order_s_for_m.vld
                & d.ready
                for di, (d, order_s_for_m) in enumerate(zip(dataOut_channels, order_din_index_for_dout))
            ])
            selected_dataOut_ready = apply_name(self, selected_dataOut_ready,
                                               "dataIn_%d_selected_dataOut_ready" % din_i)

            dataIn.ready(order_m_for_s.vld & selected_dataOut_ready)
            order_m_for_s.rd(dataIn.valid & self.get_last(dataIn) &
                             selected_dataOut_ready)

        for dout_i, (dataOut, order_s_for_m) in enumerate(zip(
                dataOut_channels, order_din_index_for_dout)):
            selected_dataIn_valid = Or(*[
                order_s_for_m.data._eq(slv_i)
                & dataIn.valid
                & order_m_for_s.vld
                & order_m_for_s.data._eq(dout_i)
                for slv_i, (dataIn, order_m_for_s) in enumerate(zip(
                    dataIn_channels, order_dout_index_for_din))
            ])
            selected_dataIn_valid = apply_name(
                self, selected_dataIn_valid,
                "dataOut_%d_selected_dataIn_valid" % dout_i)

            dataOut.valid(selected_dataIn_valid & order_s_for_m.vld)

            selected_dataIn_last = Or(*[
                dataIn.valid
                & self.get_last(dataIn)
                & order_s_for_m.vld
                & order_s_for_m.data._eq(din_i)
                for din_i, (dataIn, order_m_for_s) in enumerate(zip(
                    dataIn_channels, order_dout_index_for_din))
            ])
            selected_dataIn_last = apply_name(
                self, selected_dataIn_last,
                "dataOut_%d_selected_dataIn_last" % dout_i)

            order_s_for_m.rd(
                selected_dataIn_valid
                & selected_dataIn_last
                & dataOut.ready)

        # build data mux
        for dataOut, order_s_for_m in zip(dataOut_channels, order_din_index_for_dout):
            cases = []
            for si, s in enumerate(dataIn_channels):
                cases.append(
                    (si, connect(s, dataOut, exclude={s.valid, s.ready})))

            Switch(order_s_for_m.data)\
                .addCases(cases)\
                .Default(
                s(None)
                for s in dataOut._interfaces
                if s not in {dataOut.valid, dataOut.ready}
            )

        # connect handshake logic

    def r_handler_N_to_1(self, dataOut_channels, dataIn_channels, orderFifo_out):
        # N:1, use index of master from order_din_index_for_dout to resolve the
        # owner of data
        selectedDriverReady = Or(*[orderFifo_out.data._eq(di) & d.ready
                                   for di, d in enumerate(dataOut_channels)])
        selectedDriverReady = apply_name(
            self, selectedDriverReady, "selectedDriverReady")
        # extra enable signals based on selected driver from orderInfoFifo
        # extraHsEnableConds = {
        #                      r : fifoOut.vld  # on end of frame pop new item
        #                     }
        r = dataIn_channels[0]
        for i, d in enumerate(dataOut_channels):
            # extraHsEnableConds[d]
            d.valid(r.valid & orderFifo_out.vld & orderFifo_out.data._eq(i))
            connect(r, d, exclude=[d.valid, d.ready])

        r.ready(orderFifo_out.vld & selectedDriverReady)
        orderFifo_out.rd(r.valid & self.get_last(r) & selectedDriverReady)

    def r_handler_1_to_N(self, dataOut_channels, dataIn_channels, orderFifo_out):
        # 1:N, use index of slave from order_din_index_for_dout to resolve
        # which slave data to pick for master.r
        assert len(dataOut_channels) == 1
        m = dataOut_channels[0]
        cases = []
        for si, s in enumerate(dataIn_channels):
            cases.append((si, connect(s, m, exclude={s.valid, s.ready})))

        Switch(orderFifo_out.data)\
            .addCases(cases)\
            .Default(
            s(None)
            for s in m._interfaces
            if s not in {m.valid, m.ready}
        )

        StreamNode(
            masters=dataIn_channels,
            slaves=dataOut_channels,
            extraConds={slv: orderFifo_out.data._eq(i)
                        for i, slv in enumerate(dataIn_channels)},
            skipWhen={slv: orderFifo_out.vld & (orderFifo_out.data != i)
                      for i, slv in enumerate(dataIn_channels)},
        ).sync(enSig=orderFifo_out.vld)
        # consume item if data on slave[orderFifo_out.data].r is ready
        # and the master is ready
        selected_slave_has_last = self._sig("selected_slave_has_last")
        # reversed because of "downto"
        selected_slave_has_last(Concat(*[r.valid & self.get_last(r)
                                         for r in reversed(dataIn_channels)]
                                       )[orderFifo_out.data])
        orderFifo_out.rd(
            Or(*[r.valid for r in dataIn_channels])
            & selected_slave_has_last
            & m.ready
        )

    def _impl(self):
        propagateClkRstn(self)
        dataOut_channels = self.dataOut
        dataIn_channels = self.dataIn

        if self.REQUIRED_ORDER_SYNC_DOUT_FOR_DIN and self.REQUIRED_ORDER_SYNC_DIN_FOR_DOUT:
            # N:M,
            #  r:  for each master use slave index from order_dout_index_for_din
            #      to select the slave for each master interface
            #      and then wait until there is not index of this master
            #      on top of order_din_index_for_dout
            self.r_handler_N_to_M(
                dataOut_channels,
                dataIn_channels,
                self.order_dout_index_for_din_in,
                self.order_din_index_for_dout_in)
        elif self.REQUIRED_ORDER_SYNC_DOUT_FOR_DIN:
            # N:1,
            # r channel is connected directly to all slaves with data order synchonization
            # driven by order_din_index_for_dout
            self.r_handler_N_to_1(
                dataOut_channels,
                dataIn_channels,
                self.order_dout_index_for_din_in[0]
            )
        elif self.REQUIRED_ORDER_SYNC_DIN_FOR_DOUT:
            # 1:N, add logic which enables communication with slave only
            #      if it is selected by address
            self.r_handler_1_to_N(
                dataOut_channels,
                dataIn_channels,
                self.order_din_index_for_dout_in[0]
            )
        else:
            # 1:1, just connect
            dataOut_channels[0](dataIn_channels[0])


def example_AxiInterconnectMatrixCrossbar():
    u = AxiInterconnectMatrixCrossbar(Axi4.R_CLS)
    u.INPUT_CNT = 2
    u.OUTPUTS = [{0, 1}, {0, 1}]
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = example_AxiInterconnectMatrixCrossbar()
    print(toRtl(u))
