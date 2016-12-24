#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.synthesizer.shortcuts import toRtl
from hwtLib.samples.iLvl.ipCoreCompatibleWrap import ArrayIntfExample
from hwt.serializer.ipCoreWrapper import IpCoreWrapper


class IpCoreWrapperTC(unittest.TestCase):
    
    def test_interfaces(self):
        u = IpCoreWrapper(ArrayIntfExample())
        toRtl(u)
        self.assertTrue(hasattr(u, "a_0"))
        self.assertTrue(hasattr(u, "a_1"))
        self.assertFalse(hasattr(u, "a"))

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IpCoreWrapperTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
