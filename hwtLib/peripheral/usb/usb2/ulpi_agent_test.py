#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections  import deque
from copy import deepcopy
import unittest

from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors
from hwtLib.peripheral.usb.usb2.ulpi import Ulpi, ULPI_TX_CMD
from hwtLib.peripheral.usb.usb2.ulpi_agent import UlpiAgent
from hwtLib.peripheral.usb.usb2.ulpi_usb_agent import UlpiUsbAgent
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class UlpiWire(Unit):

    def _declr(self):
        addClkRstn(self)
        self.host = Ulpi()
        self.dev = Ulpi()._m()

    def _impl(self):
        self.dev(self.host)


class UlpiAgentBaseTC(SimTestCase):

    def assertUlpiAgNoPendingPacket(self, ag: UlpiAgent):
        self.assertIsNone(ag.actual_link_to_phy_packet)
        self.assertIsNone(ag.actual_phy_to_link_packet)

    def assertUlpiAgFinished(self, ag: UlpiAgent):
        self.assertUlpiAgNoPendingPacket(ag)
        self.assertEmpty(ag.link_to_phy_packets)
        self.assertEmpty(ag.phy_to_link_packets)


class UlpiAgentTC(UlpiAgentBaseTC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = UlpiWire()
        cls.compileSim(u)

    def format_pid_before_tx(self, pid: int):
        return int(ULPI_TX_CMD.USB_PID(pid))

    def format_link_to_phy_packets(self, packets):
        return packets

    def test_nop(self):
        self.runSim(100 * CLK_PERIOD)
        u = self.u
        self.assertUlpiAgFinished(u.host._ag)
        self.assertUlpiAgFinished(u.dev._ag)

    def test_link_to_phy(self, tx_pkt_lens=[2, 3, 2, 1, 2]):
        # dev -> host (transmit)
        u = self.u
        dev: UlpiAgent = u.dev._ag
        host: UlpiAgent = u.host._ag
        for i, pkt_len in enumerate(tx_pkt_lens):
            p = deque([self.format_pid_before_tx(i & mask(4)), ])
            p.extend(range(pkt_len))
            dev.link_to_phy_packets.append(p)

        tx_ref = deepcopy(dev.link_to_phy_packets)
        self.runSim(100 * CLK_PERIOD)
        self.assertUlpiAgFinished(dev)
        self.assertSequenceEqual(self.format_link_to_phy_packets(host.link_to_phy_packets), tx_ref)

    def test_phy_to_link(self, rx_pkt_lens=[2, 3, 2, 1, 2]):
        # host -> dev (receive)
        u = self.u
        dev: UlpiAgent = u.dev._ag
        host: UlpiAgent = u.host._ag

        for pkt_len in rx_pkt_lens:
            p = deque()
            p.extend(range(pkt_len))
            host.phy_to_link_packets.append(p)

        rx_ref = deepcopy(host.phy_to_link_packets)

        self.runSim(100 * CLK_PERIOD)
        self.assertUlpiAgFinished(u.host._ag)
        self.assertSequenceEqual(dev.phy_to_link_packets, rx_ref)

    def test_bidir(self, rx_pkt_lens=[1, 2, 3, 3, 2, 1], tx_pkt_lens=[2, 3, 2, 1, 2, 1]):
        u = self.u
        dev: UlpiAgent = u.dev._ag
        host: UlpiAgent = u.host._ag

        for i, pkt_len in enumerate(tx_pkt_lens):
            p = deque([self.format_pid_before_tx(i & mask(4)), ])
            p.extend(range(pkt_len))
            dev.link_to_phy_packets.append(p)

        tx_ref = deepcopy(dev.link_to_phy_packets)

        for pkt_len in rx_pkt_lens:
            p = deque()
            p.extend(range(pkt_len))
            host.phy_to_link_packets.append(p)

        rx_ref = deepcopy(host.phy_to_link_packets)

        self.runSim(100 * CLK_PERIOD)

        self.assertUlpiAgNoPendingPacket(host)
        self.assertUlpiAgNoPendingPacket(dev)
        self.assertEmpty(dev.link_to_phy_packets)
        self.assertEmpty(host.phy_to_link_packets)
        self.assertSequenceEqual(self.format_link_to_phy_packets(host.link_to_phy_packets), tx_ref)
        self.assertSequenceEqual(dev.phy_to_link_packets, rx_ref)


class UlpiUsbAgentTC(UlpiAgentBaseTC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = UlpiWire()
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u
        u.host._ag = UlpiUsbAgent(self.rtl_simulator, u.host)
        u.dev._ag = UlpiUsbAgent(self.rtl_simulator, u.dev)
        u.dev._ag.descriptors = get_default_usb_cdc_vcp_descriptors()

    def test_descriptor_download(self):
        self.runSim(500 * CLK_PERIOD)
        u = self.u

        self.assertUlpiAgFinished(u.dev._ag)
        self.assertUlpiAgFinished(u.host._ag)
        dev = u.dev._ag.usb_driver
        host = u.host._ag.usb_driver

        self.assertEqual(dev.addr, 1)
        self.assertEqual(len(host.descr), 1)
        self.assertSequenceEqual(host.descr[1], dev.descr)


UlpiAgent_TCs = [
    UlpiAgentTC,
    UlpiUsbAgentTC,
]

if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(UlpiAgentTC("test_phy_to_link"))
    for tc in UlpiAgent_TCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
