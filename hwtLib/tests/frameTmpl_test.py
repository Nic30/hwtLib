import unittest

from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.structUtils import HStruct_selectFields
from hwt.hdl.types.union import HUnion
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t, uint8_t
from hwtLib.types.net.eth import Eth2Header_t
from hwtLib.types.net.ip import IPv4Header_t


s_basic = HStruct(
    (uint64_t, "item0"),
    (uint64_t, "item1"),
    (uint64_t, None),
)

s_basic_srt = """<TransTmpl start:0, end:192
    <TransTmpl name:item0, start:0, end:64>
    <TransTmpl name:item1, start:64, end:128>
>"""

s_basic_3frame_srt = ["""<FrameTmpl start:0, end:64
     63                                                             0
     -----------------------------------------------------------------
0    |                             item0                             |
     -----------------------------------------------------------------
>""", """<FrameTmpl start:64, end:128
     63                                                             0
     -----------------------------------------------------------------
0    |                             item1                             |
     -----------------------------------------------------------------
>""", """<FrameTmpl start:128, end:192
     63                                                             0
     -----------------------------------------------------------------
0    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
     -----------------------------------------------------------------
>"""]

s0 = HStruct(
    (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
    (uint64_t, None),  # name = None means this field will be ignored
    (uint64_t, "item1"),
    (uint64_t, None),
    (uint16_t, "item2"),
    (uint16_t, "item3"),
    (uint32_t, "item4"),

    (uint32_t, None),
    (uint64_t, "item5"),  # this word is split on two bus words
    (uint32_t, None),

    (uint64_t, None),
    (uint64_t, None),
    (uint64_t, None),
    (uint64_t, "item6"),
    (uint64_t, "item7"),
    (HStruct(
        (uint64_t, "item0"),
        (uint64_t, "item1"),
     ), "struct0")
    )
s0at64bit_str = """<FrameTmpl start:0, end:896
     63                                                             0
     -----------------------------------------------------------------
0    |                             item0                             |
1    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
2    |                             item1                             |
3    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
4    |             item4             |     item3     |     item2     |
5    |             item5             |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
6    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|             item5             |
7    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
8    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
9    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
10   |                             item6                             |
11   |                             item7                             |
12   |                         struct0.item0                         |
13   |                         struct0.item1                         |
     -----------------------------------------------------------------
>"""

s0at71bit_str = """<FrameTmpl start:0, end:923
     70                                                                                                                                           0
     -----------------------------------------------------------------------------------------------------------------------------------------------
0    |XXXXXXXXXXXX|                                                             item0                                                             |
1    |          item1           |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
2    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|                                               item1                                               |
3    |         item3         |             item2             |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
4    |item5|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|                             item4                             | item3 |
5    |XXXXXXXXXXXXXXXXXXX|                                                          item5                                                          |
6    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
7    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
8    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
9    |   item7   |                                                             item6                                                             |X|
10   |      struct0.item0      |                                                       item7                                                       |
11   |             struct0.item1             |                                            struct0.item0                                            |
12   |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|                                     struct0.item1                                     |
     -----------------------------------------------------------------------------------------------------------------------------------------------
>"""

s1 = HStruct(
            (uint64_t[3], "arr0"),
            (uint32_t[5], "arr1")
            )

s1_str = """<FrameTmpl start:0, end:384
     63                                                             0
     -----------------------------------------------------------------
0    |                            arr0[0]                            |
1    |                            arr0[1]                            |
2    |                            arr0[2]                            |
3    |            arr1[1]            |            arr1[0]            |
4    |            arr1[3]            |            arr1[2]            |
5    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|            arr1[4]            |
     -----------------------------------------------------------------
>"""

sWithPadding = HStruct(
                       (uint64_t, "item0_0"),
                       (uint64_t, "item0_1"),
                       (uint64_t, None),
                       (uint64_t, "item1_0"),
                       (uint64_t, "item1_1"),
                       (uint64_t, None)
                       )

sWithPadding_str = """<FrameTmpl start:0, end:384
     63                                                             0
     -----------------------------------------------------------------
0    |                            item0_0                            |
1    |                            item0_1                            |
2    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
3    |                            item1_0                            |
4    |                            item1_1                            |
5    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
     -----------------------------------------------------------------
>"""

sWithPaddingMultiframe_str = [
"""<FrameTmpl start:0, end:128
     63                                                             0
     -----------------------------------------------------------------
0    |                            item0_0                            |
1    |                            item0_1                            |
     -----------------------------------------------------------------
>""",
"""<FrameTmpl start:192, end:320
     63                                                             0
     -----------------------------------------------------------------
0    |                            item1_0                            |
1    |                            item1_1                            |
     -----------------------------------------------------------------
>"""]

sWithStartPadding = HStruct(
                       (uint64_t, None),
                       (uint64_t, None),
                       (uint64_t, "item0"),
                       (uint64_t, "item1"),
                    )

sWithStartPadding_strTrim = """<FrameTmpl start:128, end:256
     63                                                             0
     -----------------------------------------------------------------
0    |                             item0                             |
1    |                             item1                             |
     -----------------------------------------------------------------
>"""

sWithStartPadding_strKept = """<FrameTmpl start:0, end:256
     63                                                             0
     -----------------------------------------------------------------
0    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
1    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
2    |                             item0                             |
3    |                             item1                             |
     -----------------------------------------------------------------
>"""

_frameHeader = HStruct(
    (Eth2Header_t, "eth"),
    (IPv4Header_t, "ipv4"),
    name="FrameHeader"
    )
frameHeader = HStruct_selectFields(_frameHeader,
                                   {"eth": {"src", "dst"},
                                    "ipv4": {"src", "dst"},
                                    })
frameHeader_str = """<FrameTmpl start:0, end:320
     63                                                             0
     -----------------------------------------------------------------
0    |    eth.src    |                    eth.dst                    |
1    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|            eth.src            |
2    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
3    |   ipv4.dst    |           ipv4.src            |XXXXXXXXXXXXXXX|
4    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|   ipv4.dst    |
     -----------------------------------------------------------------
>"""

frameHeader_split_str = [
"""<FrameTmpl start:0, end:128
     63                                                             0
     -----------------------------------------------------------------
0    |    eth.src    |                    eth.dst                    |
1    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|            eth.src            |
     -----------------------------------------------------------------
>""",
"""<FrameTmpl start:192, end:320
     63                                                             0
     -----------------------------------------------------------------
0    |   ipv4.dst    |           ipv4.src            |XXXXXXXXXXXXXXX|
1    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|   ipv4.dst    |
     -----------------------------------------------------------------
>"""
    ]

s2 = HStruct(
        (uint64_t, "item0"),
        (uint32_t, None),
        (uint64_t, "item5"),
        (uint32_t, None),
        )

s2_oneFrame = """<FrameTmpl start:0, end:192
     63                                                             0
     -----------------------------------------------------------------
0    |                             item0                             |
1    |             item5             |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
2    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|             item5             |
     -----------------------------------------------------------------
>"""

struct_with_union = HStruct(
                       (HUnion(
                         (uint8_t, "a"),
                         (uint8_t, "b"),
                        ), "u")
                    )

struct_with_union_str = """<FrameTmpl start:0, end:64
     63                                                             0
     -----------------------------------------------------------------
0    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|<union>|
0    |^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|  u.a  |
0    |^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|  u.b  |
     -----------------------------------------------------------------
>"""

union0 = HUnion(
            (HStruct(
                (uint8_t, "a0"),
                (uint8_t, "a1"),
             ), "a"),
            (uint16_t, "b"),
            )

union0_8b_str = """<FrameTmpl start:0, end:16
     7      0
     ---------
0    |<union>|
0    | a.a0  |
0    |   b   |
1    |<union>|
1    | a.a1  |
1    |   b   |
     ---------
>"""

union0_16b_str = """<FrameTmpl start:0, end:16
     15             0
     -----------------
0    |    <union>    |
0    | a.a1  | a.a0  |
0    |       b       |
     -----------------
>"""


class FrameTmplTC(unittest.TestCase):
    def test_s0at64bit(self):
        DW = 64
        tmpl = TransTmpl(s0)
        frames = list(FrameTmpl.framesFromTransTmpl(tmpl, DW))
        self.assertEqual(len(frames), 1)
        self.assertEqual(s0at64bit_str, frames[0].__repr__())

    def test_s0at71bit(self):
        DW = 71
        tmpl = TransTmpl(s0)
        frames = list(FrameTmpl.framesFromTransTmpl(tmpl, DW))
        self.assertEqual(len(frames), 1)
        self.assertEqual(s0at71bit_str, frames[0].__repr__(scale=2))

    def test_s1at64(self):
        DW = 64
        tmpl = TransTmpl(s1)
        frames = list(FrameTmpl.framesFromTransTmpl(tmpl, DW))
        self.assertEqual(len(frames), 1)
        self.assertEqual(s1_str, frames[0].__repr__())

    def test_sBasic(self):
        tmpl = TransTmpl(s_basic)
        self.assertEqual(s_basic_srt, tmpl.__repr__())

    def test_sWithPadding(self):
        DW = 64
        tmpl = TransTmpl(sWithPadding)
        frames = FrameTmpl.framesFromTransTmpl(tmpl, DW)
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(sWithPadding_str, frames[0].__repr__())

    def test_sWithPaddingMultiFrame(self):
        DW = 64
        tmpl = TransTmpl(sWithPadding)
        frames = FrameTmpl.framesFromTransTmpl(
                    tmpl,
                    DW,
                    maxPaddingWords=0,
                    trimPaddingWordsOnStart=True,
                    trimPaddingWordsOnEnd=True)
        frames = list(frames)
        self.assertEqual(len(frames), 2)
        for frame, s in zip(frames, sWithPaddingMultiframe_str):
            self.assertEqual(s, frame.__repr__())

    def test_sWithStartPadding(self):
        DW = 64
        tmpl = TransTmpl(sWithStartPadding)
        frames = FrameTmpl.framesFromTransTmpl(
                    tmpl, DW,
                    maxPaddingWords=0,
                    trimPaddingWordsOnStart=True,
                    trimPaddingWordsOnEnd=True)
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(sWithStartPadding_strTrim, frames[0].__repr__())

    def test_sWithStartPaddingKept(self):
        DW = 64
        tmpl = TransTmpl(sWithStartPadding)
        frames = FrameTmpl.framesFromTransTmpl(
                    tmpl, DW,
                    maxPaddingWords=2,
                    trimPaddingWordsOnStart=True,
                    trimPaddingWordsOnEnd=True)
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(sWithStartPadding_strKept, frames[0].__repr__())

    def test_frameHeader(self):
        DW = 64
        tmpl = TransTmpl(frameHeader)
        frames = FrameTmpl.framesFromTransTmpl(tmpl, DW)
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frameHeader_str, frames[0].__repr__())

    def test_frameHeader_splited(self):
        DW = 64
        tmpl = TransTmpl(frameHeader)
        frames = FrameTmpl.framesFromTransTmpl(
                    tmpl, DW,
                    maxPaddingWords=0,
                    trimPaddingWordsOnStart=True,
                    trimPaddingWordsOnEnd=True
                    )
        frames = list(frames)
        self.assertEqual(len(frames), 2)
        for frame, s, end in zip(frames, frameHeader_split_str, [2 * DW, 5 * DW]):
            self.assertEqual(s, frame.__repr__())
            self.assertEqual(frame.endBitAddr, end)

    def test_s2_oneFrame(self):
        DW = 64
        tmpl = TransTmpl(s2)
        frames = FrameTmpl.framesFromTransTmpl(
                    tmpl, DW,
                    )
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(repr(frames[0]), s2_oneFrame)

    def test_s2_oneFrame_tryToTrim(self):
        DW = 64
        tmpl = TransTmpl(s2)
        frames = FrameTmpl.framesFromTransTmpl(
                    tmpl, DW,
                    maxPaddingWords=0,
                    trimPaddingWordsOnStart=True,
                    trimPaddingWordsOnEnd=True
                    )
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(repr(frames[0]), s2_oneFrame)

    def test_struct_with_union(self):
        DW = 64
        tmpl = TransTmpl(struct_with_union)
        frames = FrameTmpl.framesFromTransTmpl(
                    tmpl, DW,
                    )
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(repr(frames[0]), struct_with_union_str)

    def test_union0at8b(self):
        DW = 8
        tmpl = TransTmpl(union0)
        frames = FrameTmpl.framesFromTransTmpl(tmpl, DW)
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(repr(frames[0]), union0_8b_str)

    def test_union0at16b(self):
        DW = 16
        tmpl = TransTmpl(union0)
        frames = FrameTmpl.framesFromTransTmpl(tmpl, DW)
        frames = list(frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(repr(frames[0]), union0_16b_str)

    def test_basic_tripleFrame(self):
        DW = 64
        tmpl = TransTmpl(s_basic)
        frames = FrameTmpl.framesFromTransTmpl(tmpl, DW, maxFrameLen=64)
        frames = list(frames)
        self.assertEqual(len(frames), 3)
        for f, ref in zip(frames, s_basic_3frame_srt):
            self.assertEqual(repr(f), ref)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(FrameTmplTC('test_frameHeader'))
    suite.addTest(unittest.makeSuite(FrameTmplTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
