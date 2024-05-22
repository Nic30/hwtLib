#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwtLib.abstract.template_configured import separate_streams


class TemplateConfigured_TC(unittest.TestCase):

    def test_separate_streams_simple(self):
        t = HStruct(
            (HStream(HBits(8)), "data"),
            (HBits(32), "footer"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (True, HStruct((HStream(HBits(8)), "data"),)),
            (False, HStruct((HBits(32), "footer"),))
        ])

    def test_separate_streams_no_fotter(self):
        t = HStruct(
            (HStream(HBits(8)), "data"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (True, t),
        ])

    def test_separate_streams_no_fotter2(self):
        t = HStruct(
            (HBits(8), "data"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (False, t),
        ])

    def test_separate_streams_nested(self):
        t = HStruct(
            (HStruct(
                (HStream(HBits(8)), "data"),
                (HBits(32), "footer0"),
                ), "struct"),
            (HBits(32), "footer1"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (True, HStruct(
                        (HStruct(
                            (HStream(HBits(8)), "data"),
                            ), "struct"))),
            (False, HStruct(
                    (HStruct(
                        (HBits(32), "footer0"),
                        ), "struct"),
                    (HBits(32), "footer1"),
                ))
        ])

    def test_separate_streams_simple2(self):
        t = HStruct(
            (HStream(HBits(8)), "data"),
            (HBits(32), "footer0"),
            (HBits(32), "footer1"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (True, HStruct((HStream(HBits(8)), "data"),)),
            (False, HStruct((HBits(32), "footer0"), (HBits(32), "footer1"),))
        ])

    def test_separate_streams_simple_header(self):
        t = HStruct(
            (HBits(32), "header"),
            (HStream(HBits(8)), "data"),
            (HBits(32), "footer"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (False, HStruct((HBits(32), "header"),)),
            (True, HStruct((HStream(HBits(8)), "data"))),
            (False, HStruct((HBits(32), "footer"),))
        ])


if __name__ == '__main__':
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([TemplateConfigured_TC("test_separate_streams_nested")])
    suite = testLoader.loadTestsFromTestCase(TemplateConfigured_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
