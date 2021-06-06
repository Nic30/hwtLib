#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from copy import copy
from typing import List, Tuple

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

    def setUp(self):
        SimTestCase.setUp(self)
        u: Usb2SieDeviceRx = self.u
        u.enable._ag.data.append(1)
        u.current_usb_addr._ag.data.append(0x3A)

    def test_handshake(self):
        u: Usb2SieDeviceRx = self.u

        p = self.usb.deparse_packet(UsbPacketHandshake(USB_PID.HS_ACK))
        u.rx._ag.data.append(p)

        self.runSim((len(p) + 10) * CLK_PERIOD)
        ref = [(USB_PID.HS_ACK, None, None, 0)]
        self.assertValSequenceEqual(u.rx_header._ag.data, ref)
        self.assertValSequenceEqual(u.rx_data._ag.data, [])

    def test_pid_err_no_data(self):
        u: Usb2SieDeviceRx = self.u

        p0 = deque([0])
        p1 = self.usb.deparse_packet(UsbPacketHandshake(USB_PID.HS_ACK))
        p2 = self.usb.deparse_packet(UsbPacketHandshake(USB_PID.HS_NACK))
        u.rx._ag.data.extend([p0, p1, copy(p0), p2])

        self.runSim(self.time_for_rx())
        ref = [(USB_PID.HS_ACK, None, None, 0),
               (USB_PID.HS_NACK, None, None, 0)]
        self.assertValSequenceEqual(u.rx_header._ag.data, ref)
        self.assertValSequenceEqual(u.rx_data._ag.data, [])

    def time_for_rx(self) -> int:
        u: Usb2SieDeviceRx = self.u
        return (sum(len(p) for p in u.rx._ag.data) + len(u.rx._ag.data) + 15) * CLK_PERIOD

    def test_pid_err_with_data(self):
        u: Usb2SieDeviceRx = self.u
        deparse_packet = self.usb.deparse_packet

        u.rx._ag.data.extend([
            deque([0, 0, 0]),
            deparse_packet(UsbPacketHandshake(USB_PID.HS_ACK)),
            deque([0, 0, 1, 2, 3, 0x5e, 0xf7]),
            deparse_packet(UsbPacketData(USB_PID.DATA_0, [4, 5, 6, 7])),
            deque([0, 8, 9, 10, 11]),
            deparse_packet(UsbPacketData(USB_PID.DATA_1, [12, ])),
        ])

        self.runSim(self.time_for_rx())
        ref = [
            (USB_PID.HS_ACK, None, None, 0),
            (USB_PID.DATA_0, None, None, 0),
            (USB_PID.DATA_1, None, None, 0),
        ]
        self.assertValSequenceEqual(u.rx_header._ag.data, ref)

        data_ref = []
        self.packet_data_to_rx_data_format([4, 5, 6, 7], data_ref)
        self.packet_data_to_rx_data_format([12], data_ref)
        self.assertValSequenceEqual(u.rx_data._ag.data, data_ref)

    def test_token_setup(self):
        u: Usb2SieDeviceRx = self.u
        p = self.usb.deparse_packet(UsbPacketToken(USB_PID.TOKEN_SETUP, 0x3A, 0xA))
        u.rx._ag.data.append(p)

        self.runSim((len(p) + 10) * CLK_PERIOD)
        ref = [(USB_PID.TOKEN_SETUP, 0xA, None, 0)]
        self.assertValSequenceEqual(u.rx_header._ag.data, ref)
        self.assertValSequenceEqual(u.rx_data._ag.data, [])

    def test_token_crc5_err(self):
        u: Usb2SieDeviceRx = self.u

        p0 = self.usb.deparse_packet(UsbPacketToken(USB_PID.TOKEN_SETUP, 0x3A, 0xA))
        p0[-1] = 0
        p1 = self.usb.deparse_packet(UsbPacketToken(USB_PID.TOKEN_SETUP, 0x3A, 0xB))
        u.rx._ag.data.extend([p0, p1])

        self.runSim(self.time_for_rx())
        ref = [
            (USB_PID.TOKEN_SETUP, 0, None, 1),
            (USB_PID.TOKEN_SETUP, 0xB, None, 0),
        ]
        self.assertValSequenceEqual(u.rx_header._ag.data, ref)
        self.assertValSequenceEqual(u.rx_data._ag.data, [])

    def packet_data_to_rx_data_format(self, p: List[int], res: List[Tuple[int, int, int, int]], error=False):
        if p:
            for last, d in iter_with_last(p):
                res.append((d, 1, int(error) if last else 0, int(last)))
        else:
            res.append((None, 0, int(error), 1))

    def test_data(self, packets=[[1, 2, 3, 4], [],
                                 [5, 6, 7, 8], [9, 10],
                                 [], [11], [12, 13, 14, 15], [16, 17, 18],
                                 [20, 21]
                                 ]):
        u: Usb2SieDeviceRx = self.u

        header_ref = []
        data_ref = []
        pid = USB_PID.DATA_0
        for p in packets:
            if isinstance(p, tuple):
                p, inject_crc_error, inject_len_error = p
            else:
                inject_crc_error = False
                inject_len_error = False

            _p = self.usb.deparse_packet(UsbPacketData(pid, p))
            if inject_len_error:
                _p.pop()
            elif inject_crc_error:
                _p[-1] = (_p[-1] + 1) & 0xff
            u.rx._ag.data.append(_p)

            header_ref.append((pid, None, None, 0))
            self.packet_data_to_rx_data_format(p, data_ref, error=inject_crc_error or inject_len_error)

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

    #def test_data_crc16_error(self):
    #    packets = [[1, 2, 3, 4], ([4], True, False), [],
    #               [5, 6, 7, 8], ([18, 19], True, False), [9, 10],
    #               [], [11], [12, 13, 14, 15], ([], True, False), [16, 17, 18],
    #               [20, 21]
    #               ]
    #    self.test_data(packets)

    #def test_data_len_error(self):
    def test_data_crc16_error(self):

        packets = [[1, 2, 3, 4], ([], True, True), [],
                   [5, 6, 7, 8], ([], True, True), [9, 10],
                   [], [11], [12, 13, 14, 15], ([], True, True), [16, 17, 18],
                   [20, 21]
                   ]
        self.maxDiff = None
        self.test_data(packets)


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Usb2SieDeviceRxTC("test_token_setup"))
    suite.addTest(unittest.makeSuite(Usb2SieDeviceRxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
