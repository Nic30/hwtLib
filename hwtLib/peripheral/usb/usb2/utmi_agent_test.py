#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.peripheral.usb.usb2.ulpi_agent_test import UlpiAgentTC, \
    UlpiUsbAgentTC
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbAgent
from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors


class UtmiWire(Unit):

    def _declr(self):
        addClkRstn(self)
        self.host = Utmi_8b()
        self.dev = Utmi_8b()._m()

    def _impl(self):
        self.dev(self.host)


class UtmiAgentTC(UlpiAgentTC):

    @classmethod
    def setUpClass(cls):
        cls.u = UtmiWire()
        cls.compileSim(cls.u)

    def format_pid_before_tx(self, pid: int):
        return int(pid)


class UtmiUsbAgentTC(UlpiUsbAgentTC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = UtmiWire()
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u
        u.host._ag = UtmiUsbAgent(self.rtl_simulator, u.host)
        u.dev._ag = UtmiUsbAgent(self.rtl_simulator, u.dev)
        u.dev._ag.descriptors = get_default_usb_cdc_vcp_descriptors()


UtmiAgentTCs = [
    UtmiAgentTC,
    UtmiUsbAgentTC,
]

if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(UtmiAgentTC("test_link_to_phy"))
    for tc in UtmiAgentTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
