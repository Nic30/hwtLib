#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import tempfile

from hwtLib.examples.builders.hsBuilderSplit_test import HsBuilderSplit_TC


class BasicRtlSimulatorVcdWithBuildDir(HsBuilderSplit_TC):

    @classmethod
    def setUpClass(cls):
        cls.DEFAULT_BUILD_DIR = tempfile.TemporaryDirectory().name
        super(BasicRtlSimulatorVcdWithBuildDir, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(BasicRtlSimulatorVcdWithBuildDir, cls).tearDownClass()
        shutil.rmtree(cls.DEFAULT_BUILD_DIR)


class BasicRtlSimulatorVcdWithBuildDirNoOutputDir(HsBuilderSplit_TC):
    DEFAULT_LOG_DIR = None

    @classmethod
    def setUpClass(cls):
        cls.DEFAULT_BUILD_DIR = tempfile.TemporaryDirectory().name
        super(BasicRtlSimulatorVcdWithBuildDirNoOutputDir, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(BasicRtlSimulatorVcdWithBuildDirNoOutputDir, cls).tearDownClass()
        shutil.rmtree(cls.DEFAULT_BUILD_DIR)


class BasicRtlSimulatorVcdNoBuildDirNoOutputDir(HsBuilderSplit_TC):
    DEFAULT_BUILD_DIR = None
    DEFAULT_LOG_DIR = None


BasicRtlSimulatorVcdTmpDirs_TCs = [
    BasicRtlSimulatorVcdWithBuildDir,
    BasicRtlSimulatorVcdWithBuildDirNoOutputDir,
    BasicRtlSimulatorVcdNoBuildDirNoOutputDir,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    for tc in BasicRtlSimulatorVcdTmpDirs_TCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
