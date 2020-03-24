
import unittest

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwtLib.abstract.template_configured import separate_streams


class TemplateConfigured_TC(unittest.TestCase):

    def test_separate_streams_simple(self):
        t = HStruct(
            (HStream(Bits(8)), "data"),
            (Bits(32), "footer"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (True, HStruct((HStream(Bits(8)), "data"),)),
            (False, HStruct((Bits(32), "footer"),))
        ])

    def test_separate_streams_no_fotter(self):
        t = HStruct(
            (HStream(Bits(8)), "data"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (True, t),
        ])

    def test_separate_streams_no_fotter2(self):
        t = HStruct(
            (Bits(8), "data"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (False, t),
        ])

    def test_separate_streams_nested(self):
        t = HStruct(
            (HStruct(
                (HStream(Bits(8)), "data"),
                (Bits(32), "footer0"),
                ), "struct"),
            (Bits(32), "footer1"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (True, HStruct(
                        (HStruct(
                            (HStream(Bits(8)), "data"),
                            ), "struct"))),
            (False, HStruct(
                    (HStruct(
                        (Bits(32), "footer0"),
                        ), "struct"),
                    (Bits(32), "footer1"),
                ))
        ])

    def test_separate_streams_simple2(self):
        t = HStruct(
            (HStream(Bits(8)), "data"),
            (Bits(32), "footer0"),
            (Bits(32), "footer1"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (True, HStruct((HStream(Bits(8)), "data"),)),
            (False, HStruct((Bits(32), "footer0"), (Bits(32), "footer1"),))
        ])

    def test_separate_streams_simple_header(self):
        t = HStruct(
            (Bits(32), "header"),
            (HStream(Bits(8)), "data"),
            (Bits(32), "footer"),
        )
        sep = list(separate_streams(t))
        self.assertSequenceEqual(sep, [
            (False, HStruct((Bits(32), "header"),)),
            (True, HStruct((HStream(Bits(8)), "data"))),
            (False, HStruct((Bits(32), "footer"),))
        ])


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(TemplateConfigured_TC('test_separate_streams_nested'))
    suite.addTest(unittest.makeSuite(TemplateConfigured_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
