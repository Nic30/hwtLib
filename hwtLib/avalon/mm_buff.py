#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import packIntf, \
    connectPacked
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.avalon.mm import AvalonMM
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode


@serializeParamsUniq
class AvalonMmBuff(BusBridge):
    """
    Transaction buffer for Avalon MM interface

    .. hwt-autodoc::
    """

    def _config(self):
        AvalonMM._config(self)
        self.ADDR_BUFF_DEPTH = Param(4)
        self.DATA_BUFF_DEPTH = Param(4)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.s = AvalonMM()

        with self._paramsShared():
            self.m: AvalonMM = AvalonMM()._m()

        assert self.ADDR_BUFF_DEPTH > 0 or self.DATA_BUFF_DEPTH > 0, (
            "This buffer is completely disabled,"
            " it should not be instantiated at all",
            self.ADDR_BUFF_DEPTH, self.DATA_BUFF_DEPTH)

    def _mk_buff(self, DEPTH: int, DATA_WIDTH: int) -> Union[HandshakedFifo, HandshakedReg]:
        if DEPTH == 1:
            b = HandshakedReg(Handshaked)
        else:
            b = HandshakedFifo(Handshaked)
            b.DEPTH = self.DATA_BUFF_DEPTH

        b.DATA_WIDTH = DATA_WIDTH

        return b

    def _impl(self):
        s: AvalonMM = self.s
        m: AvalonMM = self.m

        r_data = self._mk_buff(self.DATA_BUFF_DEPTH, self.DATA_WIDTH)
        self.r_data = r_data

        r_data.dataIn.data(m.readData)
        r_data.dataIn.vld(m.readDataValid)

        s.readData(r_data.dataOut.data)
        s.readDataValid(r_data.dataOut.vld)
        r_data.dataOut.rd(1)

        w_resp = self._mk_buff(self.DATA_BUFF_DEPTH, m.response._dtype.bit_length())
        self.w_resp = w_resp

        w_resp.dataIn.data(m.response)
        w_resp.dataIn.vld(m.writeResponseValid)

        s.response(w_resp.dataOut.data)
        s.writeResponseValid(w_resp.dataOut.vld)
        w_resp.dataOut.rd(1)

        addr_data = packIntf(s, exclude=[s.readData, s.readDataValid, s.response, s.writeResponseValid, s.waitRequest])
        addr = self._mk_buff(self.ADDR_BUFF_DEPTH, addr_data._dtype.bit_length())
        self.addr = addr

        addr.dataIn.data(addr_data)
        StreamNode(
            [(s.read | s.write, ~s.waitRequest), ],
            [addr.dataIn],
        ).sync()

        m_tmp = AvalonMM()
        m_tmp._updateParamsFrom(m)
        self.m_tmp = m_tmp
        non_addr_signals = [
            m_tmp.readData,
            m_tmp.readDataValid,
            m_tmp.response,
            m_tmp.writeResponseValid,
            m_tmp.waitRequest
        ]
        connectPacked(addr.dataOut.data, m_tmp, exclude=non_addr_signals)
        m(m_tmp, exclude=non_addr_signals + [m_tmp.read, m_tmp.write])
        m.read(m_tmp.read & addr.dataOut.vld)
        m.write(m_tmp.write & addr.dataOut.vld)
        addr.dataOut.rd(~m.waitRequest)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = AvalonMmBuff()
    print(to_rtl_str(u))
