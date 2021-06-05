#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.usb.constants import USB_PID
from hwtLib.peripheral.usb.sim.agent_base import UsbPacketData, \
    UsbPacketHandshake
from hwtLib.peripheral.usb.usb2.sie_tx import Usb2SieDeviceTx
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbHostProcAgent
from hwtSimApi.constants import CLK_PERIOD


class Usb2SieDeviceTxTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = Usb2SieDeviceTx()
        cls.compileSim(cls.u)
        # dummy instance of agent to just parse/deparse packets
        cls.usb = UtmiUsbHostProcAgent([], [])

    def test_handshake(self):
        u: Usb2SieDeviceTx = self.u
        u.enable._ag.data.append(1)

        pid = USB_PID.HS_ACK
        chirp = 0
        data = None
        keep = 0
        last = 1
        u.tx_cmd._ag.data.append((pid, chirp, data, keep, last))

        self.runSim(10 * CLK_PERIOD)
        ref = [list(self.usb.deparse_packet(UsbPacketHandshake(USB_PID.HS_ACK))), ]
        self.assertValSequenceEqual(u.tx._ag.data, ref)

    def test_data(self, packets=[[1, 2, 3, 4], [],
                                [5, 6, 7, 8], [9, 10],
                                [], [11], [12, 13, 14, 15], [16, 17, 18],
                                [20, 21]
                                ]):
        u: Usb2SieDeviceTx = self.u
        u.enable._ag.data.append(1)

        ref = []
        tx_cmd = u.tx_cmd._ag.data
        pid = USB_PID.DATA_0
        chirp = 0
        for p in packets:
            if p:
                keep = 1
                for last, data in iter_with_last(p):
                    u.tx_cmd._ag.data.append((pid, chirp, data, keep, last))
            else:
                last = 1
                data = None
                keep = 0
                u.tx_cmd._ag.data.append((pid, chirp, data, keep, last))

            _p = self.usb.deparse_packet(UsbPacketData(pid, p))
            ref.append(list(_p))

            if pid == USB_PID.DATA_0:
                pid = USB_PID.DATA_1
            elif pid == USB_PID.DATA_1:
                pid = USB_PID.DATA_2
            elif pid == USB_PID.DATA_2:
                pid = USB_PID.DATA_M
            elif pid == USB_PID.DATA_M:
                pid = USB_PID.DATA_0
            else:
                raise ValueError(pid)


        self.runSim((len(tx_cmd) + 4 * len(packets) + 20) * CLK_PERIOD)
        self.assertValSequenceEqual(u.tx._ag.data, ref)


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Usb2SieDeviceTxTC("test_link_to_phy"))
    suite.addTest(unittest.makeSuite(Usb2SieDeviceTxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
