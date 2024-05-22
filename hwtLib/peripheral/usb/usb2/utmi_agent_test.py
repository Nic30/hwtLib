#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors
from hwtLib.peripheral.usb.usb2.ulpi_agent_test import UlpiAgentTC, \
    UlpiUsbAgentTC
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbAgent


class UtmiWire(HwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.host = Utmi_8b()
        self.dev = Utmi_8b()._m()

    @override
    def hwImpl(self):
        self.dev(self.host)


class UtmiAgentTC(UlpiAgentTC):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = UtmiWire()
        cls.compileSim(cls.dut)

    def format_pid_before_tx(self, pid: int):
        return int(pid)


class UtmiUsbAgentTC(UlpiUsbAgentTC):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = dut = UtmiWire()
        cls.compileSim(dut)

    @override
    def setUp(self):
        SimTestCase.setUp(self)
        dut = self.dut
        dut.host._ag = UtmiUsbAgent(self.rtl_simulator, dut.host)
        dut.dev._ag = UtmiUsbAgent(self.rtl_simulator, dut.dev)
        dut.dev._ag.descriptors = get_default_usb_cdc_vcp_descriptors()


UtmiAgentTCs = [
    UtmiAgentTC,
    UtmiUsbAgentTC,
]

if __name__ == '__main__':
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([UtmiAgentTC("test_link_to_phy")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in UtmiAgentTCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
