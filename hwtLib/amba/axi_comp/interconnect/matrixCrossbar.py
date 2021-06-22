#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Set, Optional

from hwt.code import Or, Switch
from hwt.math import log2ceil
from hwt.code_utils import rename_signal
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4


class AxiInterconnectMatrixCrossbar(Unit):
    """
    Crossbar for AXI-Stream like interfaces where internal switch box
    can be driven by

    .. hwt-autodoc:: example_AxiInterconnectMatrixCrossbar
    """

    def __init__(self, intfCls, hdl_name_override:Optional[str]=None):
        self.intfCls = intfCls
        super(AxiInterconnectMatrixCrossbar, self).__init__(hdl_name_override=hdl_name_override)

    @staticmethod
    def _masters_for_slave(masters, slave_cnt) -> Dict[int, Set[int]]:
        masters_for_slave = [set() for _ in range(slave_cnt)]
        for m_i, slvs in enumerate(masters):
            for s_i in slvs:
                masters_for_slave[s_i].add(m_i)
        return masters_for_slave

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.INPUT_CNT = Param(1)
        # set of input indexes for each output
        self.OUTPUTS = Param([{0}])
        self.intfCls._config(self)

    def _declr(self):
        addClkRstn(self)
        INTF_CLS = self.intfCls
        INPUT_CNT = self.INPUT_CNT
        OUTPUT_CNT = len(self.OUTPUTS)
        self.OUTS_FOR_IN = self._masters_for_slave(self.OUTPUTS, self.INPUT_CNT)

        with self._paramsShared():
            self.dataIn = HObjList([
                INTF_CLS()
                for _ in range(INPUT_CNT)])

        with self._paramsShared():
            self.dataOut = HObjList([
                INTF_CLS()._m()
                for _ in range(OUTPUT_CNT)])

        # master index for each slave so slave knows
        # which master did read and where is should send it
        order_dout_index_for_din_in = HObjList()
        for connected_outs in self.OUTS_FOR_IN:
            if len(connected_outs) > 1:
                f = Handshaked()
                f.DATA_WIDTH = log2ceil(OUTPUT_CNT)
            else:
                f = None
            order_dout_index_for_din_in.append(f)
        self.order_dout_index_for_din_in = order_dout_index_for_din_in

        order_din_index_for_dout_in = HObjList()
        # slave index for each master
        # so master knows where it should expect the data
        for connected_ins in self.OUTPUTS:
            if len(connected_ins) > 1:
                f = Handshaked()
                f.DATA_WIDTH = log2ceil(INPUT_CNT)
            else:
                f = None
            order_din_index_for_dout_in.append(f)
        self.order_din_index_for_dout_in = order_din_index_for_dout_in

    def get_last(self, intf):
        return intf.last

    def handler_din_rd(self, dataOut_channels,
                       dataIn_channels,
                       order_dout_index_for_din,
                       order_din_index_for_dout):
        for din_i, (order_m_for_s, dataIn, connected_outputs) in enumerate(zip(
                order_dout_index_for_din, dataIn_channels, self.OUTS_FOR_IN)):
            selected_dataOut_ready = []
            for dout_i, (d, order_s_for_m) in enumerate(zip(dataOut_channels,
                                                            order_din_index_for_dout)):
                if dout_i not in connected_outputs:
                    continue
                rd = d.ready
                if order_m_for_s is not None:
                    rd = rd & order_m_for_s.data._eq(dout_i)
                if order_s_for_m is not None:
                    rd = rd & order_s_for_m.data._eq(din_i)\
                            & order_s_for_m.vld
                selected_dataOut_ready.append(rd)
            assert selected_dataOut_ready, (
                dataIn,
                "entirely disconnected from crossbar,"
                " this should have been handled before")
            selected_dataOut_ready = rename_signal(
                self, Or(*selected_dataOut_ready),
                f"dataIn_{din_i:d}_selected_dataOut_ready")
            if order_m_for_s is not None:
                dataIn.ready(order_m_for_s.vld & selected_dataOut_ready)
                order_m_for_s.rd(dataIn.valid & self.get_last(dataIn) &
                                 selected_dataOut_ready)
            else:
                dataIn.ready(selected_dataOut_ready)

    def handler_dout_vld(self, dataOut_channels,
                         dataIn_channels,
                         order_dout_index_for_din,
                         order_din_index_for_dout):
        for dout_i, (dataOut, order_s_for_m, connected_inputs) in enumerate(zip(
                dataOut_channels, order_din_index_for_dout, self.OUTPUTS)):
            selected_dataIn_valid = []
            for din_i, (dataIn, order_m_for_s) in enumerate(zip(
                    dataIn_channels, order_dout_index_for_din)):
                if din_i not in connected_inputs:
                    continue
                vld = dataIn.valid
                if order_s_for_m is not None:
                    vld = vld & order_s_for_m.data._eq(din_i)
                if order_m_for_s is not None:
                    vld = vld & order_m_for_s.vld \
                              & order_m_for_s.data._eq(dout_i)
                selected_dataIn_valid.append(vld)
            assert selected_dataIn_valid, (dataOut, "entirely disconnected from crossbar, this should have been handled before")

            selected_dataIn_valid = rename_signal(
                self, Or(*selected_dataIn_valid),
                f"dataOut_{dout_i:d}_selected_dataIn_valid")

            if order_s_for_m is None:
                dataOut.valid(selected_dataIn_valid)
            else:
                dataOut.valid(selected_dataIn_valid & order_s_for_m.vld)

            selected_dataIn_last = []
            for din_i, (dataIn, order_m_for_s) in enumerate(zip(
                    dataIn_channels, order_dout_index_for_din)):
                if din_i not in connected_inputs:
                    continue
                last = dataIn.valid & self.get_last(dataIn)
                if order_s_for_m is not None:
                    last = last & order_s_for_m.vld\
                                & order_s_for_m.data._eq(din_i)
                selected_dataIn_last.append(last)

            selected_dataIn_last = rename_signal(
                self, Or(*selected_dataIn_last),
                f"dataOut_{dout_i:d}_selected_dataIn_last")

            if order_s_for_m is not None:
                order_s_for_m.rd(
                    selected_dataIn_valid
                    & selected_dataIn_last
                    & dataOut.ready)

    def handler_data_mux(self, dataOut_channels,
                         dataIn_channels,
                         order_din_index_for_dout):
        for out_i, (dataOut, order_s_for_m) in enumerate(zip(dataOut_channels,
                                                             order_din_index_for_dout)):
            if order_s_for_m is None:
                connected_in = self.OUTPUTS[out_i]
                assert len(connected_in) == 1, connected_in
                connected_in = list(connected_in)[0]
                dataOut(dataIn_channels[connected_in],
                        exclude={dataOut.valid, dataOut.ready})
            else:
                cases = []
                for si, s in enumerate(dataIn_channels):
                    cases.append(
                        (si, dataOut(s, exclude={s.valid, s.ready})))

                Switch(order_s_for_m.data)\
                    .add_cases(cases)\
                    .Default(
                    s(None)
                    for s in dataOut._interfaces
                    if s not in {dataOut.valid, dataOut.ready}
                )

    def connection_handler_N_to_M(
            self,
            dataOut_channels,
            dataIn_channels,
            order_dout_index_for_din,
            order_din_index_for_dout):
        self.handler_din_rd(dataOut_channels, dataIn_channels,
                            order_dout_index_for_din, order_din_index_for_dout)
        self.handler_dout_vld(dataOut_channels, dataIn_channels,
                              order_dout_index_for_din, order_din_index_for_dout)
        self.handler_data_mux(dataOut_channels, dataIn_channels,
                              order_din_index_for_dout)

    def _impl(self):
        propagateClkRstn(self)
        dataOut_channels = self.dataOut
        dataIn_channels = self.dataIn
        # N:M,
        #  for each master use slave index from order_dout_index_for_din
        #  to select the slave for each master interface
        #  and then wait until there is not index of this master
        #  on top of order_din_index_for_dout
        # N:1,
        #  channel is connected directly to all slaves with data order synchonization
        #  driven by order_din_index_for_dout
        # 1:N, add logic which enables communication with slave only
        #      if it is selected by address
        # 1:1, just connect
        self.connection_handler_N_to_M(
            dataOut_channels,
            dataIn_channels,
            self.order_dout_index_for_din_in,
            self.order_din_index_for_dout_in)


def example_AxiInterconnectMatrixCrossbar():
    u = AxiInterconnectMatrixCrossbar(Axi4.R_CLS)
    u.INPUT_CNT = 2
    u.OUTPUTS = [{0, 1}, {0, 1}]
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = example_AxiInterconnectMatrixCrossbar()
    print(to_rtl_str(u))
