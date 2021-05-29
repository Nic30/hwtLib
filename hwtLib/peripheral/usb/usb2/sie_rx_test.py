#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.usb.constants import USB_PID
from hwtLib.peripheral.usb.sim.agent_base import UsbPacketToken, UsbPacketData, \
    UsbPacketHandshake
from hwtLib.peripheral.usb.usb2.sie_rx import Usb2SieDeviceRx
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbHostProcAgent
from hwtSimApi.constants import CLK_PERIOD


class Usb2SieDeviceRxTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = Usb2SieDeviceRx()
        cls.compileSim(cls.u)
        # dummy instance of agent to just parse/deparse packets
        cls.usb = UtmiUsbHostProcAgent([], [])

    def test_handshake(self):
        u: Usb2SieDeviceRx = self.u
        u.enable._ag.data.append(1)
        u.current_usb_addr._ag.data.append(0x3A)

        p = self.usb.deparse_packet(UsbPacketHandshake(USB_PID.HS_ACK))
        u.rx._ag.data.append(p)

        self.runSim((len(p) + 10) * CLK_PERIOD)
        ref = [(USB_PID.HS_ACK, None, None, 0)]
        self.assertValSequenceEqual(u.rx_header._ag.data, ref)
        self.assertValSequenceEqual(u.rx_data._ag.data, [])

    def test_token_setup(self):
        u: Usb2SieDeviceRx = self.u
        u.enable._ag.data.append(1)
        u.current_usb_addr._ag.data.append(0x3A)

        p = self.usb.deparse_packet(UsbPacketToken(USB_PID.TOKEN_SETUP, 0x3A, 0xA))
        u.rx._ag.data.append(p)

        self.runSim((len(p) + 10) * CLK_PERIOD)
        ref = [(USB_PID.TOKEN_SETUP, 0xA, None, 0)]
        self.assertValSequenceEqual(u.rx_header._ag.data, ref)
        self.assertValSequenceEqual(u.rx_data._ag.data, [])

    def test_data(self, packets=[[1, 2, 3, 4], [],
                                 [5, 6, 7, 8], [9, 10],
                                 [], [11], [12, 13, 14, 15], [16, 17, 18],
                                 [20, 21]
                                 ]):
        u: Usb2SieDeviceRx = self.u
        u.enable._ag.data.append(1)

        header_ref = []
        data_ref = []
        pid = USB_PID.DATA_0
        for p in packets:
            _p = self.usb.deparse_packet(UsbPacketData(pid, p))
            u.rx._ag.data.append(_p)

            header_ref.append((pid, None, None, 0))
            if p:
                for last, d in iter_with_last(p):
                    data_ref.append((d, 1, 0, int(last)))
            else:
                data_ref.append((None, 0, 0, 1))

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

        self.runSim((len(data_ref) + 4 * len(packets) + 20) * CLK_PERIOD)
        self.assertValSequenceEqual(u.rx_header._ag.data, header_ref)
        self.assertValSequenceEqual(u.rx_data._ag.data, data_ref)


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Usb2SieDeviceRxTC("test_link_to_phy"))
    suite.addTest(unittest.makeSuite(Usb2SieDeviceRxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
