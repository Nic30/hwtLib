
import unittest

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwtLib.abstract.template_configured import separate_footers


class TemplateConfigured_TC(unittest.TestCase):

    def test_separate_footers_simple(self):
        t = HStruct(
            (HStream(Bits(8)), "data"),
            (Bits(32), "footer"),
        )
        m = {}
        sep = list(separate_footers(t, m))
        self.assertSequenceEqual(sep, [
            (False, HStruct((HStream(Bits(8)), "data"),)),
            (True, HStruct((Bits(32), "footer"),))
        ])

    def test_separate_footers_no_fotter(self):
        t = HStruct(
            (HStream(Bits(8)), "data"),
        )
        m = {}
        sep = list(separate_footers(t, m))
        self.assertSequenceEqual(sep, [
            (False, t),
        ])

    def test_separate_footers_no_fotter2(self):
        t = HStruct(
            (Bits(8), "data"),
        )
        m = {}
        sep = list(separate_footers(t, m))
        self.assertSequenceEqual(sep, [
            (True, t),
        ])

    def test_separate_footers_nested(self):
        t = HStruct(
            (HStruct(
                (HStream(Bits(8)), "data"),
                (Bits(32), "footer0"),
                ), "struct"),
            (Bits(32), "footer1"),
        )
        m = {}
        sep = list(separate_footers(t, m))
        self.assertSequenceEqual(sep, [
            (False, HStruct(
                        (HStruct(
                            (HStream(Bits(8)), "data"),
                            ), "struct"))),
            (True, HStruct(
                    (HStruct(
                        (Bits(32), "footer0"),
                        ), "struct"),
                    (Bits(32), "footer1"),
                ))
        ])

    def test_separate_footers_simple2(self):
        t = HStruct(
            (HStream(Bits(8)), "data"),
            (Bits(32), "footer0"),
            (Bits(32), "footer1"),
        )
        m = {}
        sep = list(separate_footers(t, m))
        self.assertSequenceEqual(sep, [
            (False, HStruct((HStream(Bits(8)), "data"),)),
            (True, HStruct((Bits(32), "footer0"), (Bits(32), "footer1"),))
        ])

    def test_separate_footers_simple_header(self):
        t = HStruct(
            (Bits(32), "header"),
            (HStream(Bits(8)), "data"),
            (Bits(32), "footer"),
        )
        m = {}
        sep = list(separate_footers(t, m))
        self.assertSequenceEqual(sep, [
            (False, HStruct((Bits(32), "header"), (HStream(Bits(8)), "data"),)),
            (True, HStruct((Bits(32), "footer"),))
        ])


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(TemplateConfigured_TC('test_separate_footers_nested'))
    suite.addTest(unittest.makeSuite(TemplateConfigured_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
