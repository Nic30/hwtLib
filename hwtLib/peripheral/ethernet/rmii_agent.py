from collections import deque

from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from hwt.pyUtils.arrayQuery import grouper
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator
from typing import List
from pyMathBitPrecise.bit_utils import get_bit_range
from hwtLib.peripheral.ethernet.constants import ETH
from itertools import chain


class RmiiAgent(AgentBase):
    def __init__(self, sim: HdlSimulator, intf):
        AgentBase.__init__(self, sim, intf)
        intf.ref_clk._initSimAgent(sim)
        intf.rx._initSimAgent(sim)
        intf.tx._initSimAgent(sim)

    def getDrivers(self):
        raise NotImplementedError()

    def getMonitors(self):
        i = self.intf
        return [
           *i.ref_clk._ag.getDrivers(),
           *i.tx._ag.getMonitors(),
           *i.rx._ag.getDrivers(),
        ]


class RmiiTxChannelAgent(VldSyncedAgent):
    """
    Simulation agent for :class:`hwtLib.peripheral.ethernet.rmii.RmiiTxChannel` interface

    :type intf: RmiiTxChannel
    """
    def __init__(self, sim: HdlSimulator, intf, allowNoReset=False):
        VldSyncedAgent.__init__(self, sim, intf, allowNoReset=allowNoReset)
        self.is_monitor = False
        self.actual_frame = []
        self.frames = deque()

    def getMonitors(self):
        self.is_monitor = True
        return VldSyncedAgent.getMonitors(self)

    def _pop_frame(self):
        data = self.data
        assert len(data) % 4 == 0, (len(data), data)
        frame = []
        for b01, b23, b45, b67 in grouper(4, data):
            b = (int(b67) << 6) | (int(b45) << 4) | (int(b23) << 2) | int(b01)
            frame.append(b)
        return frame

    def get_data(self):
        return self.intf.d.read()

    def set_data(self, data):
        self.intf.d.write(data)

    @classmethod
    def get_valid_signal(cls, intf):
        return intf.en

    def get_valid(self):
        v = self._vld.read()
        if not int(v):
            # this is potential end of frame
            if self.data:
                self.frames.append(self._pop_frame())
                self.data = deque()
        return v

    def set_valid(self, val):
        self._lastVld = val
        return self._vld.write(val)


class RmiiRxChannelAgent(VldSyncedAgent):
    """
    Simulation agent for :class:`hwtLib.peripheral.ethernet.rmii.RmiiRxChannel` interface

    :type intf: RmiiRxChannel
    """

    def _append_frame(self, frame: List[int], add_preamble=True):
        data = self.data
        if add_preamble:
            preamble = [
                0x0,
                *[int(ETH.PREAMBLE_1B) for _ in range(7)],
                int(ETH.SFD),
            ]
            frame = chain(preamble, frame)

        for b in frame:
            b01 = b & 0b11
            b23 = get_bit_range(b, 2, 2)
            b45 = get_bit_range(b, 4, 2)
            b67 = get_bit_range(b, 6, 2)
            data.extend([b01, b23, b45, b67])

    def get_data(self):
        return self.intf.d.read()

    def set_data(self, data):
        self.intf.d.write(data)

    @classmethod
    def get_valid_signal(cls, intf):
        return intf.crs_dv

    def get_valid(self):
        return self._vld.read()

    def set_valid(self, val):
        self._lastVld = val
        return self._vld.write(val)
