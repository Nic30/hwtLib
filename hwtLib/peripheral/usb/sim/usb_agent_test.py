#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
import unittest

from hwtLib.peripheral.usb.constants import USB_PID, USB_VER
from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors
from hwtLib.peripheral.usb.descriptors.std import usb_descriptor_device_t, \
    usb_descriptor_device_qualifier_t, usb_descriptor_configuration_t, \
    usb_descriptor_interface_t
from hwtLib.peripheral.usb.sim.agent_base import UsbPacketData, UsbPacketToken
from hwtLib.peripheral.usb.sim.usb_agent_device import UsbDevAgent
from hwtLib.peripheral.usb.sim.usb_agent_host import UsbHostAgent


# from hwtLib.peripheral.usb.descriptors.hid import usb_descriptor_hid_t
class UsbAgentTC(unittest.TestCase):

    def test_crc16_data(self):
        p = UsbPacketData(USB_PID.DATA_1, [
            0x11, 0x22, 0x33, 0x44, 0x55, 0x66,
            0x77, 0x88, 0x99, 0x00, 0xAA, 0xBB,
            0xCC, 0xDD, 0xEE, 0xFF,
        ])
        self.assertEqual(p.crc16(), 0x4748)

        p = UsbPacketData(USB_PID.DATA_1, [
            0x00, 0x01, 0x02, 0x03,
        ])
        self.assertEqual(p.crc16(), 0xf75e)

        p = UsbPacketData(USB_PID.DATA_1, [
            0x23, 0x45, 0x67, 0x89
        ])
        self.assertEqual(p.crc16(), 0x7038)

    def test_crc5_token(self):
        p = UsbPacketToken(USB_PID.TOKEN_IN, 3, 0)
        self.assertEqual(p.crc5(), 0x0A)

        p = UsbPacketToken(USB_PID.TOKEN_IN, 0x3a, 0xA)
        self.assertEqual(p.crc5(), 0x1C)

        p = UsbPacketToken(USB_PID.TOKEN_IN, 0x3a, 0xB)
        self.assertEqual(p.crc5(), 0x11)

        p = UsbPacketToken(USB_PID.TOKEN_IN, 0x15, 0xe)
        self.assertEqual(p.crc5(), 0x17)

    def test_descriptor_sizes(self):
        self.assertEqual(usb_descriptor_device_t.bit_length() // 8, 18)
        self.assertEqual(usb_descriptor_device_qualifier_t.bit_length() // 8, 10)
        self.assertEqual(usb_descriptor_configuration_t.bit_length() // 8, 9)
        self.assertEqual(usb_descriptor_interface_t.bit_length() // 8, 9)
        # self.assertEqual(usb_descriptor_hid_t.bit_length() // 8, 9)

    def test_USB_VER_encode(self):
        self.assertEqual(USB_VER.to_uint16_t(USB_VER.USB1_1), 0x0110)

    def test_device_enumeration_and_descriptor_download(self):
        rx = deque()
        tx = deque()

        host = UsbHostAgent(rx, tx)
        dev = UsbDevAgent(tx, rx, get_default_usb_cdc_vcp_descriptors())
        for a in [host, dev]:
            a.RETRY_CNTR_MAX = 100
        h_done = False
        d_done = False
        h = host.proc()
        d = dev.proc()
        it_limit = int(10e3)
        while not h_done and it_limit:
            if not d_done:
                try:
                    next(d)
                except StopIteration:
                    d_done = True
            if not h_done:
                try:
                    next(h)
                except StopIteration:
                    h_done = True
            it_limit -= 1
        self.assertGreater(it_limit, 0, "sim timeout check")

        self.assertSequenceEqual(rx, [])
        self.assertSequenceEqual(tx, [])
        self.assertEqual(dev.addr, 1)
        self.assertEqual(len(host.descr), 1)
        self.assertSequenceEqual(host.descr[1], dev.descr)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(FrameTmplTC('test_frameHeader_trimmed'))
    suite.addTest(unittest.makeSuite(UsbAgentTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
