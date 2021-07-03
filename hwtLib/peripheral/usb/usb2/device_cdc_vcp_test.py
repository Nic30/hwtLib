#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.usb.constants import USB_VER
from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors
from hwtLib.peripheral.usb.usb2.device_cdc_vcp import Usb2CdcVcp
from hwtLib.peripheral.usb.usb2.ulpi_agent_test import UlpiAgentBaseTC
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbAgent
from hwtSimApi.constants import CLK_PERIOD


class Usb2CdcVcpTC(UlpiAgentBaseTC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = Usb2CdcVcp()
        u.PRE_NEGOTIATED_TO = USB_VER.USB2_0  # to avoid waiting at the begin of sim
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u
        u.phy._ag = UtmiUsbAgent(u.phy._ag.sim, u.phy)
        u.phy._ag.RETRY_CNTR_MAX = 100

    def test_descriptor_download(self):
        self.runSim(600 * CLK_PERIOD)
        u = self.u

        self.assertUlpiAgFinished(u.phy._ag)
        host = u.phy._ag.usb_driver

        # self.assertEqual(dev.addr, 1)
        self.assertEqual(len(host.descr), 1)
        self.assertSequenceEqual(host.descr[1],
                                 get_default_usb_cdc_vcp_descriptors(productStr="Usb2CdcVcp",
                                                                     bMaxPacketSize=512))


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Usb2CdcVcpTC("test_phy_to_link"))
    suite.addTest(unittest.makeSuite(Usb2CdcVcpTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
