#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.peripheral.usb.usb2.ulpi_agent_test import UlpiAgentTC
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b


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


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(UtmiAgentTC("test_link_to_phy"))
    suite.addTest(unittest.makeSuite(UtmiAgentTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
